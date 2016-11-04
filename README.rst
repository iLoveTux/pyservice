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

Basically, you create an application class which inherits from
`pyservice.PyService` and override the `started` and `stoped` methods.
You can also optionally override the `installed` and `uninstalled` methods
in order to perform and reverse any preparations which may need to be done
when your service is installed or uninstalled.

If you care about the details:

On Linux a script is placed in `/etc/init.d/$name` where $name is the
name of your service when it is installed. When it is being started a
pidfile is created in `~/.pyservice_pids` and when it is stopped the
pidfile is removed.

On Windows, it is installed as a normal windows service and can be controlled
either through the command line or through the Windows Services application
after it is installed.

Show me the code!
-----------------

Here is a simple example of an echo server created using twisted and turned
into a service:

.. code:: python

    import pyservice
    import tornado.ioloop
    import tornado.web
    import sys

    class TestHandler(tornado.web.RequestHandler):
        def get(self):
            self.write('Hello world!')

    class MyService(pyservice.PyService):
        def started(self):
            application = tornado.web.Application([
                (r'/', TestHandler)
            ])

            application.listen(1337)
            tornado.ioloop.IOLoop.instance().start()

        def stopped(self):
            sys.exit(0)

        def installed(self):
            pass

        def uninstalled(self):
            pass

    if __name__ == '__main__':
        MyService('myservice', 'My nice little test service', True)


**NOTE**

On systemd systems, like Fedora, RHEL and CentOS you will either need to
reboot or reload systemd. I recommend a reboot as it seems to lead to more
solid results, but in case you can't you can use the following command:

..code:: bash

    $ sudo systemctl daemon-reload

The reason for this is that we are targeting maximum portability with the
least amount of code and systemd includes a utility which will translate
our sys v init script into a systemd unit. 
