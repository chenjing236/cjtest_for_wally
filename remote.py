class RemoteRunner(object):
    """
    Class to provide a utils.run-like method to execute command on
    remote host or guest. Provide a similar interface with utils.run
    on local.
    """

    def __init__(self, client="ssh", host=None, port="22", username="root",
                 password=None, prompt=r"[\#\$]\s*$", linesep="\n",
                 log_filename=None, timeout=240, internal_timeout=10,
                 session=None, use_key=False):
        """
        Initialization of RemoteRunner. Init a session login to remote host or
        guest.

        :param client: The client to use ('ssh', 'telnet' or 'nc')
        :param host: Hostname or IP address
        :param port: Port to connect to
        :param username: Username (if required)
        :param password: Password (if required)
        :param prompt: Shell prompt (regular expression)
        :param linesep: The line separator to use when sending lines
                (e.g. '\\n' or '\\r\\n')
        :param log_filename: If specified, log all output to this file
        :param timeout: Total time duration to wait for a successful login
        :param internal_timeout: The maximal time duration (in seconds) to wait
                for each step of the login procedure (e.g. the "Are you sure"
                prompt or the password prompt)
        :param session: An existing session
        :see: wait_for_login()
        :raise: Whatever wait_for_login() raises
        """
        self.host = host
        self.username = username
        self.password = password
        if session is None:
            if host is None:
                raise exceptions.TestError(
                    "Neither host, nor session was defined!")
            self.session = wait_for_login(client, host, port, username,
                                          password, prompt, linesep,
                                          log_filename, timeout,
                                          internal_timeout, use_key=use_key)
        else:
            self.session = session
        # Init stdout pipe and stderr pipe.
        random_pipe = utils_misc.generate_random_string(6)
        self.stdout_pipe = '/tmp/cmd_stdout_%s' % random_pipe
        self.stderr_pipe = '/tmp/cmd_stderr_%s' % random_pipe

    def run(self, command, timeout=60, ignore_status=False, internal_timeout=None):
        """
        Method to provide a utils.run-like interface to execute command on
        remote host or guest.

        :param timeout: Total time duration to wait for command return.
        :param ignore_status: If ignore_status=True, do not raise an exception,
                              no matter what the exit code of the command is.
                              Else, raise CmdError if exit code of command is not
                              zero.
        """
        # Redirect the stdout and stderr to file, Deviding error message
        # from output, and taking off the color of output. To return the same
        # result with utils.run() function.
        command = "%s 1>%s 2>%s" % (
            command, self.stdout_pipe, self.stderr_pipe)
        status, _ = self.session.cmd_status_output(command, timeout=timeout,
                                                   internal_timeout=internal_timeout)
        output = self.session.cmd_output("cat %s;rm -f %s" %
                                         (self.stdout_pipe, self.stdout_pipe))
        errput = self.session.cmd_output("cat %s;rm -f %s" %
                                         (self.stderr_pipe, self.stderr_pipe))
        cmd_result = process.CmdResult(command=command, exit_status=status,
                                       stdout=output, stderr=errput)
        if status and (not ignore_status):
            raise process.CmdError(command, cmd_result)
        return cmd_result

