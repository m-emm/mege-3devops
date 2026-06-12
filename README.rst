.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/mege-3devops.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/mege-3devops
    .. image:: https://readthedocs.org/projects/mege-3devops/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://mege-3devops.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/mege-3devops/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/mege-3devops
    .. image:: https://img.shields.io/pypi/v/mege-3devops.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/mege-3devops/
    .. image:: https://img.shields.io/conda/vn/conda-forge/mege-3devops.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/mege-3devops
    .. image:: https://pepy.tech/badge/mege-3devops/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/mege-3devops
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/mege-3devops

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

============
mege-3devops
============


    Add a short description here!


A longer description of your project goes here...


Mege Ender 3 V3 KE IDEX Print Areas
====================================

The live IDEX conversion currently has two slicer-facing X envelopes:

* T0 single-tool prints may use ``X=-30..244``.
* Dual tool-switch prints must use the shared area ``X=0..244``.
* Both modes use ``Y=0..290`` and ``Z=0..294``.

The generic ``SAFE_*`` constants in
``mege_3devops.process_data.mege_ender_3v3ke_idex`` intentionally refer to
the dual tool-switch area. T0-only jobs should use the explicit
``T0_SINGLE_*`` constants or ``T0_SINGLE_PRINT_AREA``.


.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
