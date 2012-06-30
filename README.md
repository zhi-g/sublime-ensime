# Sublime ENSIME

This project provides an integration with ENSIME and Sublime Text Editor 2.
Big thanks to Aemon Cannon, Daniel Spiewak, Ivan Porto Carrero and Michael Nash,
whose work and inspiration helped to kicked off this project.

## How to install?

1. Install the package itself:

    a. If you use [Package Control](http://wbond.net/sublime_packages/package_control),
    add repository https://github.com/sublimescala/sublime-ensime and install package sublime-ensime.

    b. Otherwise, in your Sublime Text `Packages` dir (you can find it by `Preferences -> Browse Packages`),

    ```
    git clone git://github.com/sublimescala/sublime-ensime.git sublime-ensime
    ```

2. Install Ensime.

    a. In Unix (including Mac OS X), `cd` into the just created `sublime-ensime` directory and run
    ```
    ./install-ensime-server.sh
    ```

    b. In Windows, just download the version of Ensime listed in the `./install-ensime-server` file
    from https://github.com/sublimescala/ensime/downloads. It will contain a directory with the same
    name as Ensime version. Extract it into the just created `sublime-ensime` directory and rename
    to `server`.

3. (Re)start Sublime Text editor.

Once you're in a project that has a .ensime file in the root folder, you can start a server from the file context menu. Or run:

```python
window.run_command("ensime_server", { "start": True })
```

## Project status

SublimeScala project is an early alpha. Some basic things might work (for example, error highlighting), but basically anything might blow up in your face. Please, submit issues to our tracker if you catch SublimeScala doing that: https://github.com/sublimescala/sublime-ensime/issues/new.

Also note that SublimeScala uses pre-release Scala compiler (which roughly corresponds to 2.10.0-M4). This might also produce funny bugs. Use our bug reporting facility to report those: https://issues.scala-lang.org/secure/CreateIssue!default.jspa.

Anyways this venture is very important for the project maintainers, since we use Scala every day, so we'll do our best to release something workable within a few months (ideally, before the final release of Scala 2.10.0).

The first release will include go to definition (aka ctrl+click), on-the-fly error highlighting (it sort of works right now) and type inspection of program fragments. We'd also love to add debugging facilities at some point in the future.