
from optparse import OptionParser
import sys

from command import *
from err import *


class ParseArgs(object):

    def __init__(self,groot):
        self.groot = groot


    def parse(self,args):
        self.options, cmd_name, cmd_args = self.parse_pre_cmd_args(args)
        self.build_cmd(cmd_name,cmd_args)
        return self


    def parse_pre_cmd_args(self,args):
        """ Parse all the args up to the command name """
        try:
            op = OptionParser(usage="%prog [options] <command> [command options]")
            op.disable_interspersed_args()
            op.add_option("-r", "--repo", "--root",
                          action="store", type="string", dest="repo")
            op.add_option("-q", "--quiet",
                          action="callback", callback=self.set_quiet,
                          help="suppress normal status messages")
            op.add_option("-v", "--verbose",
                          action="callback", callback=self.set_verbose,
                          help="include extra verbose output")
            op.add_option("--debug",
                          action="callback", callback=self.set_debug,
                          help="include extra debugging output")
            op.add_option("--in", type="string", dest="in_")

            options, args = op.parse_args(args)

            if len(args) == 0:
                raise InvalidUsage("Missing command")
            cmd_name = args.pop(0)

            return (options, cmd_name, args)
        
        except InvalidUsage, ex:
            print("ERROR: %s" % ex.args[0])
            op.print_usage()
            sys.exit(1)


    def set_quiet(self, option, opt_str, value, parser, *args, **kwargs):
        self.groot.quiet = True
        
    def set_verbose(self, option, opt_str, value, parser, *args, **kwargs):
        self.groot.verbose = True
        
    def set_debug(self, option, opt_str, value, parser, *args, **kwargs):
        self.groot.quiet = False
        self.groot.verbose = True
        self.groot.debug_mode = True
        

    def build_cmd(self,cmd_name,cmd_args):
        """ Instantiate the command handler by this command name,
            and check the command-specific arguments """
        try:
            if self.options.in_:
                cmd_args[0:0] = [self.options.in_,cmd_name]
                cmd_name = 'in'

            cmd_class = BaseCommand.find_command(cmd_name)
            if not cmd_class:
                raise InvalidUsage("Unknown command: %s" % cmd_name)
            self.command = cmd_class(self.groot,cmd_name)
            self.command.parse_args(cmd_args)

        except InvalidUsage, ex:
            print("ERROR: %s" % ex.args[0])
            sys.exit(1)
            

