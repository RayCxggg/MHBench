import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Iterator

from config.config import Config


@contextmanager
def _temporary_tfvars(config: Config) -> Iterator[str]:
    """Create a throwaway tfvars file for Terraform and clean it up afterwards."""
    terraform_vars = config.terraform_vars
    tfvars_content = "\n".join(
        f"{key} = {json.dumps(value)}" for key, value in terraform_vars.items()
    )

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".tfvars", delete=False, encoding="utf-8"
    )
    try:
        tmp_file.write(tfvars_content)
        tmp_file.flush()
        tmp_file.close()
        yield tmp_file.name
    finally:
        try:
            os.remove(tmp_file.name)
        except OSError:
            pass


TOPOLOGIES_DIR = "src/environments/terraform/topologies"


def _run_terraform(name: str, command: str, config: Config) -> None:
    deployment_dir = os.path.join(TOPOLOGIES_DIR, name)
    init = subprocess.run(
        ["terraform", "init"],
        cwd=deployment_dir,
        capture_output=True,
        text=True,
    )
    if init.returncode != 0:
        raise RuntimeError(f"terraform init failed in {deployment_dir}:\n{init.stderr}")

    with _temporary_tfvars(config) as tfvars_path:
        process = subprocess.Popen(
            [
                "terraform",
                command,
                f"-var-file={tfvars_path}",
                "-auto-approve",
            ],
            cwd=deployment_dir,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        stdout, _ = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"terraform {command} failed in {deployment_dir}:\n{stdout}")


def deploy_network(name: str, config: Config) -> None:
    _run_terraform(name, "apply", config)


def destroy_network(name: str, config: Config) -> None:
    _run_terraform(name, "destroy", config)


def _state_resource_ids(name: str, resource_type: str | None = None) -> set[str]:
    """IDs of resources tracked in a topology's local Terraform state."""
    state_path = os.path.join(TOPOLOGIES_DIR, name, "terraform.tfstate")
    if not os.path.exists(state_path):
        return set()
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)

    ids = set()
    for resource in state.get("resources", []):
        if resource.get("mode") != "managed":
            continue
        if resource_type and resource.get("type") != resource_type:
            continue
        for instance in resource.get("instances", []):
            resource_id = instance.get("attributes", {}).get("id")
            if resource_id:
                ids.add(resource_id)
    return ids


def deployed_topologies() -> list[str]:
    """Topologies whose Terraform state still tracks live resources."""
    return [
        name
        for name in sorted(os.listdir(TOPOLOGIES_DIR))
        if _state_resource_ids(name)
    ]


def managed_resource_ids(resource_type: str) -> set[str]:
    """IDs of resources of the given type created by any MHBench topology."""
    ids = set()
    for name in deployed_topologies():
        ids |= _state_resource_ids(name, resource_type)
    return ids
