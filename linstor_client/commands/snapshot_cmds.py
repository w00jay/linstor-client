import linstor_client.argparse.argparse as argparse

import linstor_client
from linstor_client.commands import Commands
from linstor_client.consts import Color
from linstor.sharedconsts import FLAG_DELETE, FLAG_SUCCESSFUL, FLAG_FAILED_DEPLOYMENT, FLAG_FAILED_DISCONNECT
from linstor_client.utils import Output
from linstor import SizeCalc


class SnapshotCommands(Commands):
    class Rollback(object):
        LONG = "rollback"
        SHORT = "rb"

    def __init__(self):
        super(SnapshotCommands, self).__init__()

    def setup_commands(self, parser):
        subcmds = [
            Commands.Subcommands.Create,
            Commands.Subcommands.List,
            Commands.Subcommands.Delete,
            self.Rollback,
            Commands.Subcommands.Resource,
            Commands.Subcommands.VolumeDefinition
        ]

        # Snapshot subcommands
        snapshot_parser = parser.add_parser(
            Commands.SNAPSHOT,
            aliases=["s"],
            formatter_class=argparse.RawTextHelpFormatter,
            description="Snapshot subcommands")
        snapshot_subp = snapshot_parser.add_subparsers(
            title="shapshot commands",
            metavar="",
            description=Commands.Subcommands.generate_desc(subcmds)
        )

        # new snapshot
        p_new_snapshot = snapshot_subp.add_parser(
            Commands.Subcommands.Create.LONG,
            aliases=[Commands.Subcommands.Create.SHORT],
            description='Creates a snapshot of a resource.')
        p_new_snapshot.add_argument(
            '--async',
            action='store_true',
            help='Do not wait for deployment on satellites before returning'
        )
        p_new_snapshot.add_argument(
            'node_name',
            type=str,
            nargs='*',
            help='Names of the nodes where the snapshot should be created. '
                 'If none are given, the snapshot will be taken on all nodes '
                 'where the given resources is present.'
        ).completer = self.node_completer
        p_new_snapshot.add_argument(
            'resource_definition_name',
            type=str,
            help='Name of the resource definition').completer = self.resource_dfn_completer
        p_new_snapshot.add_argument(
            'snapshot_name',
            type=str,
            help='Name of the snapshot local to the resource definition')
        p_new_snapshot.set_defaults(func=self.create)

        # delete snapshot
        p_delete_snapshot = snapshot_subp.add_parser(
            Commands.Subcommands.Delete.LONG,
            aliases=[Commands.Subcommands.Delete.SHORT],
            description='Deletes a snapshot.')
        p_delete_snapshot.add_argument(
            'resource_definition_name',
            type=str,
            help='Name of the resource definition').completer = self.resource_dfn_completer
        p_delete_snapshot.add_argument(
            'snapshot_name',
            type=str,
            help='Name of the snapshot local to the resource definition')
        p_delete_snapshot.set_defaults(func=self.delete)

        # roll back to snapshot
        p_rollback_snapshot = snapshot_subp.add_parser(
            self.Rollback.LONG,
            aliases=[self.Rollback.SHORT],
            description='Rolls resource data back to snapshot state. '
                        'The resource must not be in use. '
                        'The snapshot will not be removed and can be used for subsequent rollbacks. '
                        'Only the most recent snapshot may be used; '
                        'to roll back to an earlier snapshot, the intermediate snapshots must first be deleted.')
        p_rollback_snapshot.add_argument(
            'resource_definition_name',
            type=str,
            help='Name of the resource definition').completer = self.resource_dfn_completer
        p_rollback_snapshot.add_argument(
            'snapshot_name',
            type=str,
            help='Name of the snapshot local to the resource definition')
        p_rollback_snapshot.set_defaults(func=self.rollback)

        # list snapshot definitions
        p_lsnapshots = snapshot_subp.add_parser(
            Commands.Subcommands.List.LONG,
            aliases=[Commands.Subcommands.List.SHORT],
            description=' Prints a list of all snapshots known to linstor. '
                        'By default, the list is printed as a human readable table.')
        p_lsnapshots.add_argument('-p', '--pastable', action="store_true", help='Generate pastable output')
        p_lsnapshots.set_defaults(func=self.list)

        # volume definition commands
        volume_definition_subcmds = [
            Commands.Subcommands.Restore
        ]

        volume_definition_parser = snapshot_subp.add_parser(
            Commands.Subcommands.VolumeDefinition.LONG,
            formatter_class=argparse.RawTextHelpFormatter,
            aliases=[Commands.Subcommands.VolumeDefinition.SHORT],
            description="%s subcommands" % Commands.Subcommands.VolumeDefinition.LONG)

        volume_definition_subp = volume_definition_parser.add_subparsers(
            title="%s subcommands" % Commands.Subcommands.VolumeDefinition.LONG,
            metavar="",
            description=Commands.Subcommands.generate_desc(volume_definition_subcmds))

        # restore resource from snapshot
        p_restore_volume_definition = volume_definition_subp.add_parser(
            Commands.Subcommands.Restore.LONG,
            aliases=[Commands.Subcommands.Restore.SHORT],
            description='Creates volume definitions from a snapshot. '
                        'Only the basic structure is restored, that is volume numbers and sizes. '
                        'Additional configuration such as properties is not restored.')
        p_restore_volume_definition.add_argument(
            '--from-resource', '--fr',
            required=True,
            type=str,
            help='Name of the resource definition containing the snapshot').completer = self.resource_dfn_completer
        p_restore_volume_definition.add_argument(
            '--from-snapshot', '--fs',
            required=True,
            type=str,
            help='Name of the snapshot to restore from')
        p_restore_volume_definition.add_argument(
            '--to-resource', '--tr',
            required=True,
            type=str,
            help='Name of the resource definition in which to create the volume definitions'
        ).completer = self.resource_dfn_completer
        p_restore_volume_definition.set_defaults(func=self.restore_volume_definition)

        # resource commands
        resource_subcmds = [
            Commands.Subcommands.Restore
        ]

        resource_parser = snapshot_subp.add_parser(
            Commands.Subcommands.Resource.LONG,
            formatter_class=argparse.RawTextHelpFormatter,
            aliases=[Commands.Subcommands.Resource.SHORT],
            description="%s subcommands" % Commands.Subcommands.Resource.LONG)

        resource_subp = resource_parser.add_subparsers(
            title="%s subcommands" % Commands.Subcommands.Resource.LONG,
            metavar="",
            description=Commands.Subcommands.generate_desc(resource_subcmds))

        # restore resource from snapshot
        p_restore_snapshot = resource_subp.add_parser(
            Commands.Subcommands.Restore.LONG,
            aliases=[Commands.Subcommands.Restore.SHORT],
            description='Restores a snapshot on a node. '
                        'Creates a new resource initialized with the data from a given snapshot. '
                        'The volume definitions of the target resource must match those from the snapshot.')
        p_restore_snapshot.add_argument(
            'node_name',
            type=str,
            nargs='*',
            help='Names of the nodes where the snapshot should be restored. '
                 'If none are given, resources will be created on all nodes where the snapshot is present.'
        ).completer = self.node_completer
        p_restore_snapshot.add_argument(
            '--from-resource', '--fr',
            required=True,
            type=str,
            help='Name of the resource definition containing the snapshot').completer = self.resource_dfn_completer
        p_restore_snapshot.add_argument(
            '--from-snapshot', '--fs',
            required=True,
            type=str,
            help='Name of the snapshot to restore from')
        p_restore_snapshot.add_argument(
            '--to-resource', '--tr',
            required=True,
            type=str,
            help='Name of the resource definition in which to create the resource from this snapshot'
        ).completer = self.resource_dfn_completer
        p_restore_snapshot.set_defaults(func=self.restore)

        self.check_subcommands(snapshot_subp, subcmds)

    def create(self, args):
        async_flag = vars(args)["async"]
        replies = self._linstor.snapshot_create(
            args.node_name, args.resource_definition_name, args.snapshot_name, async_flag)
        return self.handle_replies(args, replies)

    def restore_volume_definition(self, args):
        replies = self._linstor.snapshot_volume_definition_restore(
            args.from_resource, args.from_snapshot, args.to_resource)
        return self.handle_replies(args, replies)

    def restore(self, args):
        replies = self._linstor.snapshot_resource_restore(
            args.node_name, args.from_resource, args.from_snapshot, args.to_resource)
        return self.handle_replies(args, replies)

    def delete(self, args):
        replies = self._linstor.snapshot_delete(args.resource_definition_name, args.snapshot_name)
        return self.handle_replies(args, replies)

    def rollback(self, args):
        replies = self._linstor.snapshot_rollback(args.resource_definition_name, args.snapshot_name)
        return self.handle_replies(args, replies)

    @classmethod
    def show(cls, args, lstmsg):
        tbl = linstor_client.Table(utf8=not args.no_utf8, colors=not args.no_color, pastable=args.pastable)
        tbl.add_column("ResourceName")
        tbl.add_column("SnapshotName")
        tbl.add_column("NodeNames")
        tbl.add_column("Volumes")
        tbl.add_column("State", color=Output.color(Color.DARKGREEN, args.no_color))
        for snapshot_dfn in lstmsg.snapshots:
            if FLAG_DELETE in snapshot_dfn.flags:
                state_cell = tbl.color_cell("DELETING", Color.RED)
            elif FLAG_FAILED_DEPLOYMENT in snapshot_dfn.flags:
                state_cell = tbl.color_cell("Failed", Color.RED)
            elif FLAG_FAILED_DISCONNECT in snapshot_dfn.flags:
                state_cell = tbl.color_cell("Satellite disconnected", Color.RED)
            elif FLAG_SUCCESSFUL in snapshot_dfn.flags:
                state_cell = tbl.color_cell("Successful", Color.DARKGREEN)
            else:
                state_cell = tbl.color_cell("Incomplete", Color.DARKBLUE)

            tbl.add_row([
                snapshot_dfn.resource_name,
                snapshot_dfn.name,
                ", ".join([node_name for node_name in snapshot_dfn.nodes]),
                ", ".join([
                    str(snapshot_vlm_dfn.number) + ": " + SizeCalc.approximate_size_string(snapshot_vlm_dfn.size)
                    for snapshot_vlm_dfn in snapshot_dfn.snapshot_volume_definitions]),
                state_cell
            ])
        tbl.show()

    def list(self, args):
        lstmsg = self._linstor.snapshot_dfn_list()

        return self.output_list(args, lstmsg, self.show)
