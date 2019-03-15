import copy
import torch

from catalyst.dl.utils import UtilsFactory
from .utils import soft_update


class Algorithm:
    def __init__(
        self,
        critic,
        gamma,
        n_step,
        critic_optimizer_params,
        critic_grad_clip_params=None,
        critic_loss_params=None,
        critic_scheduler_params=None,
        resume=None,
        load_optimizer=True,
        critic_tau=1.0,
        **kwargs
    ):
        # hack to prevent cycle dependencies
        from catalyst.contrib.registry import Registry

        self._device = UtilsFactory.prepare_device()

        self.critic = critic.to(self._device)
        self.target_critic = copy.deepcopy(critic).to(self._device)

        self.critic_optimizer = Registry.get_optimizer(
            self.critic, **critic_optimizer_params
        )

        self.critic_optimizer_params = critic_optimizer_params

        critic_scheduler_params = critic_scheduler_params or {}

        self.critic_scheduler = Registry.get_scheduler(
            self.critic_optimizer, **critic_scheduler_params
        )

        self.critic_scheduler_params = critic_scheduler_params

        self.n_step = n_step
        self.gamma = gamma

        critic_grad_clip_params = critic_grad_clip_params or {}

        self.critic_grad_clip_fn = Registry.get_grad_clip_fn(
            **critic_grad_clip_params
        )

        self.critic_grad_clip_params = critic_grad_clip_params

        self.critic_criterion = Registry.get_criterion(
            **(critic_loss_params or {})
        )

        self.critic_loss_params = critic_loss_params

        self.critic_tau = critic_tau

        self._init(**kwargs)

        if resume is not None:
            self.load_checkpoint(resume, load_optimizer=load_optimizer)

    def _init(self, **kwargs):
        assert len(kwargs) == 0

    def __repr__(self):
        str_val = " ".join(
            [
                f"{key}: {str(getattr(self, key, ''))}"
                for key in ["n_step", "gamma", "critic_tau"]
            ]
        )
        return f"Algorithm. {str_val}"

    def _to_tensor(self, *args, **kwargs):
        return torch.Tensor(*args, **kwargs).to(self._device)

    def update_step(self, value_loss, critic_update=True):
        "updates parameters of neural networks and returns learning metrics"
        raise NotImplementedError

    def train(self, batch, actor_update=False, critic_update=True):
        states_t, actions_t, rewards_t, states_tp1, done_t = \
            batch["state"], batch["action"], batch["reward"], \
            batch["next_state"], batch["done"]

        states_t = self._to_tensor(states_t)
        actions_t = self._to_tensor(actions_t).type(torch.LongTensor)
        rewards_t = self._to_tensor(rewards_t).unsqueeze(1)
        states_tp1 = self._to_tensor(states_tp1)
        done_t = self._to_tensor(done_t).unsqueeze(1)

        value_loss = self._loss_fn(
            states_t, actions_t, rewards_t, states_tp1, done_t
        )

        metrics = self.update_step(
            value_loss=value_loss,
            critic_update=critic_update
        )

        return metrics

    def get_td_errors(self, batch):
        # @TODO: for prioritized replay
        raise NotImplementedError

    def critic_update(self, loss):
        self.critic.zero_grad()
        self.critic_optimizer.zero_grad()
        loss.backward()
        if self.critic_grad_clip_fn is not None:
            self.critic_grad_clip_fn(self.critic.parameters())
        self.critic_optimizer.step()
        if self.critic_scheduler is not None:
            self.critic_scheduler.step()
            return {"lr_critic": self.critic_scheduler.get_lr()[0]}

    def target_critic_update(self):
        soft_update(self.target_critic, self.critic, self.critic_tau)

    def prepare_checkpoint(self):
        checkpoint = {}

        for key in ["critic"]:
            checkpoint[f"{key}_state_dict"] = getattr(self, key).state_dict()
            for key2 in ["optimizer", "scheduler"]:
                key2 = f"{key}_{key2}"
                value2 = getattr(self, key2, None)
                if value2 is not None:
                    checkpoint[f"{key2}_state_dict"] = value2.state_dict()

        return checkpoint

    def load_checkpoint(self, filepath, load_optimizer=True):
        checkpoint = UtilsFactory.load_checkpoint(filepath)
        for key in ["critic"]:
            value_l = getattr(self, key, None)
            if value_l is not None:
                value_r = checkpoint[f"{key}_state_dict"]
                value_l.load_state_dict(value_r)

            if load_optimizer:
                for key2 in ["optimizer", "scheduler"]:
                    key2 = f"{key}_{key2}"
                    value_l = getattr(self, key2, None)
                    if value_l is not None:
                        value_r = checkpoint[f"{key2}_state_dict"]
                        value_l.load_state_dict(value_r)

    @classmethod
    def prepare_for_trainer(cls, config):
        # hack to prevent cycle dependencies
        from catalyst.contrib.registry import Registry

        config_ = config.copy()

        state_shape = (
            config_["shared"]["history_len"],
            config_["shared"]["observation_size"],
        )
        num_actions = config_["shared"]["num_actions"]
        n_step = config_["shared"]["n_step"]
        gamma = config_["shared"]["gamma"]
        history_len = config_["shared"]["history_len"]
        trainer_state_shape = (config_["shared"]["observation_size"], )
        trainer_action_shape = (config_["shared"]["num_actions"], )

        critic_fn = config_["critic"].pop("agent", None)
        critic = Registry.get_agent(
            agent=critic_fn,
            state_shape=state_shape,
            **config_["critic"]
        )

        algorithm = cls(
            **config_["algorithm"],
            critic=critic,
            n_step=n_step,
            gamma=gamma
        )

        kwargs = {
            "algorithm": algorithm,
            "state_shape": trainer_state_shape,
            "action_shape": trainer_action_shape,
            "n_step": n_step,
            "gamma": gamma,
            "history_len": history_len
        }

        return kwargs

    @classmethod
    def prepare_for_sampler(cls, config):
        # hack to prevent cycle dependencies
        from catalyst.contrib.registry import Registry

        config_ = config.copy()

        state_shape = (
            config_["shared"]["history_len"],
            config_["shared"]["observation_size"],
        )
        num_actions = config_["shared"]["num_actions"]

        critic_fn = config_["critic"].pop("agent", None)
        critic = Registry.get_agent(
            agent=critic_fn,
            state_shape=state_shape,
            **config_["critic"]
        )

        history_len = config_["shared"]["history_len"]

        kwargs = {"critic": critic, "history_len": history_len}

        return kwargs
