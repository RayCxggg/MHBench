from pydantic import BaseModel, model_validator


class ElasticSearchConfig(BaseModel):
    api_key: str
    port: int


class C2Config(BaseModel):
    api_key: str
    port: int
    external: bool = False
    python_path: str
    caldera_path: str


class OpenstackConfig(BaseModel):
    ssh_key_name: str
    ssh_key_path: str
    openstack_region: str
    openstack_auth_url: str
    perry_key_name: str | None = None

    # Authenticate with either username/password/project or an application
    # credential (required on clouds with federated login, e.g. Jetstream2).
    project_name: str | None = None
    openstack_username: str | None = None
    openstack_password: str | None = None
    application_credential_id: str | None = None
    application_credential_secret: str | None = None

    # Cloud-specific names; defaults match the DevStack/Kolla setup scripts
    host_flavor: str = "p2.tiny"
    manage_flavor: str = "m1.small"
    attacker_flavor: str = "m1.small"
    external_network: str = "external"

    # Teardown of generated environments deletes every resource in the
    # project. Only enable on a project dedicated to MHBench.
    allow_project_wide_cleanup: bool = False

    @model_validator(mode="after")
    def check_auth(self):
        if self.uses_application_credential:
            if not self.application_credential_secret:
                raise ValueError("application_credential_secret is required")
        elif not (
            self.project_name and self.openstack_username and self.openstack_password
        ):
            raise ValueError(
                "Provide application_credential_id/secret or "
                "project_name/openstack_username/openstack_password"
            )
        return self

    @property
    def uses_application_credential(self) -> bool:
        return self.application_credential_id is not None

    def to_terraform_vars(self) -> dict[str, str | None]:
        """Render the Terraform variable mapping expected by our modules."""
        perry_key = self.perry_key_name or self.ssh_key_name
        return {
            "project_name": self.project_name,
            "openstack_username": self.openstack_username,
            "openstack_password": self.openstack_password,
            "application_credential_id": self.application_credential_id,
            "application_credential_secret": self.application_credential_secret,
            "openstack_region": self.openstack_region,
            "openstack_auth_url": self.openstack_auth_url,
            "perry_key_name": perry_key,
            "host_flavor": self.host_flavor,
            "manage_flavor": self.manage_flavor,
            "attacker_flavor": self.attacker_flavor,
            "external_network": self.external_network,
        }


class Config(BaseModel):
    elastic_config: ElasticSearchConfig
    c2_config: C2Config | None = None
    openstack_config: OpenstackConfig
    external_ip: str
    experiment_timeout_minutes: int

    @property
    def terraform_vars(self) -> dict[str, str | None]:
        """Expose Terraform variables derived from the OpenStack config."""
        return self.openstack_config.to_terraform_vars()
