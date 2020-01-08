import os
import sys
import datetime
if sys.version_info >= (3, 0):
    import faulthandler
    faulthandler.enable()

# -- pyvista configuration ---------------------------------------------------
import pyvista
import numpy as np
# Manage errors
pyvista.set_error_output_file('errors.txt')
# Ensure that offscreen rendering is used for docs generation
pyvista.OFF_SCREEN = True # Not necessary - simply an insurance policy
# Preferred plotting style for documentation
pyvista.set_plot_theme('document')
pyvista.rcParams['window_size'] = np.array([1024, 768]) * 2
# Save figures in specified directory
pyvista.FIGURE_PATH = os.path.join(os.path.abspath('./images/'), 'auto-generated/')
if not os.path.exists(pyvista.FIGURE_PATH):
    os.makedirs(pyvista.FIGURE_PATH)

# -- General configuration ------------------------------------------------
numfig = False
html_show_sourcelink = False
html_logo = './_static/pyvista_logo.png'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.doctest',
              'sphinx.ext.autosummary',
              'notfound.extension',
              'sphinx_copybutton',
              'sphinx_gallery.gen_gallery',
              'sphinx.ext.extlinks',
              ]


linkcheck_retries = 3
linkcheck_timeout = 500

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'PyVista'
year = datetime.date.today().year
copyright = u'2017-{}, The PyVista Developers'.format(year)
author = u'Alex Kaszynski and Bane Sullivan'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = pyvista.__version__

# The full version, including alpha/beta/rc tags.
release = pyvista.__version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'friendly'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Sphinx Gallery Options
from sphinx_gallery.sorting import FileNameSortKey

sphinx_gallery_conf = {
    # path to your examples scripts
    "examples_dirs": [
        "../examples/",
    ],
    # path where to save gallery generated examples
    "gallery_dirs": ["examples"],
    # Patter to search for example files
    "filename_pattern": r"\.py",
    # Remove the "Download all examples" button from the top level gallery
    "download_all_examples": False,
    # Sort gallery example by file name instead of number of lines (default)
    "within_subsection_order": FileNameSortKey,
    # directory where function granular galleries are stored
    "backreferences_dir": None,
    # Modules for which function level galleries are created.  In
    "doc_module": "pyvista",
    "image_scrapers": ('pyvista', 'matplotlib'),
    'first_notebook_cell': ("%matplotlib inline\n"
                            "from pyvista import set_plot_theme\n"
                            "set_plot_theme('document')"),
}


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_context = {
    # Enable the "Edit in GitHub link within the header of each page.
    'display_github': True,
    # Set the following variables to generate the resulting github URL for each page.
    # Format Template: https://{{ github_host|default("github.com") }}/{{ github_user }}/{{ github_repo }}/blob/{{ github_version }}{{ conf_py_path }}{{ pagename }}{{ suffix }}
    'github_user': 'pyvista',
    'github_repo': 'pyvista',
    'github_version': 'master/docs/',
    'menu_links_name': 'Getting Connected',
    'menu_links': [
        ('<i class="fa fa-slack fa-fw"></i> Slack Community', 'http://slack.pyvista.org'),
        ('<i class="fa fa-comment fa-fw"></i> Support', 'https://github.com/pyvista/pyvista-support'),
        ('<i class="fa fa-github fa-fw"></i> Source Code', 'https://github.com/pyvista/pyvista'),
        ('<i class="fa fa-gavel fa-fw"></i> Contributing', 'https://github.com/pyvista/pyvista/blob/master/CONTRIBUTING.md'),
        ('<i class="fa fa-file-text fa-fw"></i> The Paper', 'https://doi.org/10.21105/joss.01450'),
    ],
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'logo_only': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'pyvistadoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'point_size': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'pyvista.tex', u'pyvista Documentation',
     author, 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'pyvista', u'pyvista Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'pyvista', u'pyvista Documentation',
     author, 'pyvista', 'A Streamlined Python Interface for the Visualization Toolkit',
     'Miscellaneous'),
]

# -- Custom 404 page

notfound_context = {
        'body': '<h1>Page not found.</h1>\n\nPerhaps try the <a href="http://docs.pyvista.org/examples/index.html">examples page</a>.',
}
notfound_no_urls_prefix = True


# -- Autosummary options
from sphinx.ext.autosummary import Autosummary
from sphinx.ext.autosummary import get_documenter
from docutils.parsers.rst import directives
from sphinx.util.inspect import safe_getattr

class AutoAutoSummary(Autosummary):

    option_spec = {
        'methods': directives.unchanged,
        'attributes': directives.unchanged,
    }

    required_arguments = 1
    app = None

    @staticmethod
    def get_members(obj, typ, include_public=None):
        if not include_public:
            include_public = []
        items = []
        for name in sorted(obj.__dict__.keys()):#dir(obj):
            try:
                documenter = get_documenter(AutoAutoSummary.app, safe_getattr(obj, name), obj)
            except AttributeError:
                continue
            if documenter.objtype in typ:
                items.append(name)
        public = [x for x in items if x in include_public or not x.startswith('_')]
        return public, items

    def run(self):
        clazz = str(self.arguments[0])
        try:
            (module_name, class_name) = clazz.rsplit('.', 1)
            m = __import__(module_name, globals(), locals(), [class_name])
            c = getattr(m, class_name)
            if 'methods' in self.options:
                _, methods = self.get_members(c, ['method'], ['__init__'])
                self.content = ["~%s.%s" % (clazz, method) for method in methods if not method.startswith('_')]
            if 'attributes' in self.options:
                _, attribs = self.get_members(c, ['attribute', 'property'])
                self.content = ["~%s.%s" % (clazz, attrib) for attrib in attribs if not attrib.startswith('_')]
        except:
            print('Something went wrong when autodocumenting {}'.format(clazz))
        finally:
            return super(AutoAutoSummary, self).run()

def setup(app):
    AutoAutoSummary.app = app
    app.add_directive('autoautosummary', AutoAutoSummary)
    app.add_stylesheet("style.css")
    app.add_stylesheet("copybutton.css")
