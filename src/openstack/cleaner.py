from openstack.connection import Connection
from src.utility.openstack_helper_functions import teardown_helper
import time


class OpenstackCleaner:
    def __init__(
        self, openstack_conn: Connection, allow_project_wide_cleanup: bool = False
    ):
        self.openstack_conn = openstack_conn
        self.allow_project_wide_cleanup = allow_project_wide_cleanup

    def clean_environment(self):
        if not self.allow_project_wide_cleanup:
            raise RuntimeError(
                "Cleaning a generated environment deletes every server, floating IP, "
                "router, network and security group in the OpenStack project. Set "
                "openstack_config.allow_project_wide_cleanup to true only if the "
                "project is dedicated to MHBench."
            )

        print("Tearing down...")

        conn = self.openstack_conn

        teardown_helper.delete_instances(conn)
        while conn.list_servers():
            time.sleep(0.5)

        teardown_helper.delete_floating_ips(conn)
        while conn.list_floating_ips():
            time.sleep(0.5)

        teardown_helper.delete_routers(conn)
        while conn.list_routers():
            time.sleep(0.5)

        teardown_helper.delete_subnets(conn)
        teardown_helper.delete_networks(conn)
        teardown_helper.delete_security_groups(conn)
