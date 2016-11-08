PyService - A Cross-Platform service library
============================================

**NOTE** This is a fork of the original, I am working to get this up
to my own personal standards as I will be making extensive use of this
library. When I am finished, I will submit a pull-request to see if the
original author agrees with and is interested in incorporating my changes.

If he is not, I will support this fork of the project seperately.

If you would like to participate and contribute to this project, please
feel free to open issues and submit pull requests against this fork and
they will all be included if the original author wishes to merge the results.

What is this and why should I care?
-----------------------------------

This is a library which makes it very easy to create services on virtually
any consumer operating system (Mac OSx coming soon). What is a service, you
ask? Well, a service is a computer program which runs in the background and
can be set to start on boot. Think of a web server...if you created a web
server you would presumably want to have the capability to start that server
automatically whenever the machine running on it reboots.

Now I know what you're saying, "All my apps live in the cloud, I don't need
to worry about these types of things" and you might be right, but there are
those of us who are either worried about our privacy or work for companies
who care about their privacy and security. That being said, this is not a
security framework or anything like that, but insourcing all of your
applications (if done well) can eliminate many potential security and
privacy concerns.

How does it work?
-----------------

Basically, you create define a function and wrap it in the service
decorator provided by this library. Then, safely wrapped in a
'if __name__ == "__main__":' block, you call "handle_cli()" and pass
in your callable. That's it.

If you care about the details:

On Linux a script is placed in `/etc/init.d/$name` where $name is the
name of your service when it is installed. When it is being started a
pidfile is created in `/var/run/$name` and when it is stopped the
pidfile is removed.

On Windows, it is installed as a normal windows service and can be controlled
either through the command line or through the Windows Services application
after it is installed.

**NOTE**

On systemd systems, like Fedora, RHEL and CentOS you will either need to
reboot or reload systemd. I recommend a reboot as it seems to lead to more
solid results, but in case you can't you can use the following command:

..code:: bash

    $ sudo systemctl daemon-reload

The reason for this is that we are targeting maximum portability with the
least amount of code and systemd includes a utility which will translate
our sys v init script into a systemd unit. 

Show me the code!
-----------------

Here is a simple example which will write the current time to a file
every minute:

.. code:: python

    from pyservice import service, handle_cli
    import time
    
    @service
    def time_writer(self):
        while not self.stop_requested:
            with open("/tmp/times.txt", "w") as fp:
                fp.write(time.ctime(time.time) + "\n")
            time.sleep(60)
    
    if __name__ == "__main__":
        handle_cli(time_writer)

Here is a simple example of an echo server created using twisted and turned
into a service:

.. code:: python

    from pyservice import service, handle_cli
    import tornado.ioloop
    import tornado.web

    class TestHandler(tornado.web.RequestHandler):
        def get(self):
            self.write('Hello world!')

    @service
    def tornado_server(self):
        application = tornado.web.Application([
            (r'/', TestHandler)
        ])

        application.listen(1337)
        tornado.ioloop.IOLoop.instance().start()

    if __name__ == '__main__':
        handle_cli(tornado_server)

Contributing
------------

You can do all of the usual github things like submitting issues and
pull requests. For code submissions, please try to adhere to PEP 8 and
please try to include unit tests for your enhancements and bug fixes.

