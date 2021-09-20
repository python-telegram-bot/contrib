How To Contribute
=================

Every open source project lives from the generous contributions of developers who invest their spare time and ``ptbcontrib`` is no different. To make participation as pleasant as possible, this project adheres to the `Code of Conduct`_ by the Python Software Foundation.

Setting things up
-----------------

1. Fork the ``ptbcontrib`` repository to your GitHub account.

2. Clone your forked repository of ``ptbcontrib`` to your computer:

   .. code-block:: bash

      $ git clone https://github.com/<your username>/ptbcontrib --recursive
      $ cd ptbcontrib

3. Add a track to the original repository:

   .. code-block:: bash

      $ git remote add upstream https://github.com/python-telegram-bot/ptbcontrib

4. Install dependencies:

   .. code-block:: bash

      $ pip install -r requirements.txt -r requirements-dev.txt


5. Install pre-commit hooks:

   .. code-block:: bash

      $ pre-commit install

Finding something to do
#######################

If you already know what you'd like to work on, you can skip this section.

If you have an idea for something to do, first check if it's already been filed on the `issue tracker`_. If so, add a comment to the issue saying you'd like to work on it, and we'll help you get started! Otherwise, please file a new issue and assign yourself to it.

Instructions for making a code change
#####################################

The central development branch is ``main``, which should be clean and ready for release at any time. In general, all changes should be done as feature branches based off of ``main``.

Here's how to make a one-off code change.

1. **Choose a descriptive branch name.** It should be lowercase, hyphen-separated, and a noun describing the change (so, ``fuzzy-rules``, but not ``implement-fuzzy-rules``). Also, it shouldn't start with ``hotfix`` or ``release``.

2. **Create a new branch with this name, starting from** ``main``. In other words, run:

   .. code-block:: bash

      $ git fetch upstream
      $ git checkout main
      $ git merge upstream/main
      $ git checkout -b your-branch-name

3. **Make a commit to your feature branch**. Each commit should be self-contained and have a descriptive commit message that helps other developers understand why the changes were made.

   - In case you want to add a new contribution to the library, it should be placed in its own directory beneath ``ptbcontrib`` and contain a README file. This directory may also contain a file ``requirements.txt`` listing any requirements of your contribution. Have a look at the existing contributions for inspiration.

   - You can refer to relevant issues in the commit message by writing, e.g., "#105".

   - Your code should adhere to the `PEP 8 Style Guide`_, with the exception that we have a maximum line length of 99.

   - Provide static typing with signature annotations. The documentation of `MyPy`_ will be a good start, the cheat sheet is `here`_.

   - Document your code through docstrings. Have a look at the existing modules for inspirations.

   - For consistency, please conform to `Google Python Style Guide`_ and `Google Python Style Docstrings`_.

   - The following exceptions to the above (Google's) style guides applies:

    - Documenting types of global variables and complex types of class members can be done using the Sphinx docstring convention.

   -  In addition, ``ptbcontrib`` uses the `Black`_ coder formatting. Plugins for Black exist for some `popular editors`_. You can use those instead of manually formatting everything.

   - Please ensure that the code you write is well-tested. For new contributions, please create a new file ``tests/test_{yourcontribution}.py`` for the tests.

   - Don’t break backward compatibility.

   - Before making a commit ensure that all automated tests still pass:

     .. code-block::

        $ python run_tests.py -c

     The script `run_tests.py` is a wrapper around the `pytest` module. This is needed, because the different contributions may have different dependencies that need to be installed before running tests. For more details on the script run

     .. code-block::

        $ python run_tests.py -h

   - To actually make the commit (this will trigger tests for black, lint and pep8 automatically):

     .. code-block:: bash

        $ git add your-file-changed.py

   - black may change code formatting, make sure to re-add them to your commit.

     .. code-block:: bash

      $ git commit -a -m "your-commit-message-here"

   - Finally, push it to your GitHub fork, run:

     .. code-block:: bash

      $ git push origin your-branch-name

4. **When your feature is ready to merge, create a pull request.**

   - Go to your fork on GitHub, select your branch from the dropdown menu, and click "New pull request".

   - Add a descriptive comment explaining the purpose of the branch (e.g. "Add the a helper to date pick via an inline keyboard."). This will tell the reviewer what the purpose of the branch is.

   - Click "Create pull request". An admin will assign a reviewer to your commit.

5. **Address review comments until all reviewers give LGTM ('looks good to me').**

   - When your reviewer has reviewed the code, you'll get an email. You'll need to respond in two ways:

       - Make a new commit addressing the comments you agree with, and push it to the same branch. Ideally, the commit message would explain what the commit does (e.g. "Fix lint error"), but if there are lots of disparate review comments, it's fine to refer to the original commit message and add something like "(address review comments)".

       - In addition, please reply to each comment. Each reply should be either "Done" or a response explaining why the corresponding suggestion wasn't implemented. All comments must be resolved before LGTM can be given.

   - Resolve any merge conflicts that arise. To resolve conflicts between 'your-branch-name' (in your fork) and 'main' (in the ``ptbcontrib`` repository), run:

     .. code-block:: bash

        $ git checkout your-branch-name
        $ git fetch upstream
        $ git merge upstream/main
        $ ...[fix the conflicts]...
        $ ...[make sure the tests pass before committing]...
        $ git commit -a
        $ git push origin your-branch-name

   - At the end, the reviewer will merge the pull request.

6. **Tidy up!** Delete the feature branch from both your local clone and the GitHub repository:

   .. code-block:: bash

      $ git branch -D your-branch-name
      $ git push origin --delete your-branch-name

7. **Celebrate.** Congratulations, you have contributed to ``ptbcontrib``!

Style commandments
------------------

Assert comparison order
#######################

- assert statements should compare in **actual** == **expected** order.
For example (assuming ``test_call`` is the thing being tested):

.. code-block:: python

    # GOOD
    assert test_call() == 5

    # BAD
    assert 5 == test_call()

Properly calling callables
##########################

Methods, functions and classes can specify optional parameters (with default
values) using Python's keyword arg syntax. When providing a value to such a
callable we prefer that the call also uses keyword arg syntax. For example:

.. code-block:: python

   # GOOD
   f(0, optional=True)

   # BAD
   f(0, True)

This gives us the flexibility to re-order arguments and more importantly
to add new required arguments. It's also more explicit and easier to read.

.. _`Code of Conduct`: https://www.python.org/psf/codeofconduct/
.. _`issue tracker`: https://github.com/python-telegram-bot/ptbcontrib/issues
.. _`Telegram group`: https://telegram.me/pythontelegrambotgroup
.. _`PEP 8 Style Guide`: https://www.python.org/dev/peps/pep-0008/
.. _`Google Python Style Guide`: http://google.github.io/styleguide/pyguide.html
.. _`Google Python Style Docstrings`: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
.. _`MyPy`: https://mypy.readthedocs.io/en/stable/index.html
.. _`here`: https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
.. _`Black`: https://black.readthedocs.io/en/stable/index.html
.. _`popular editors`: https://black.readthedocs.io/en/stable/editor_integration.html
