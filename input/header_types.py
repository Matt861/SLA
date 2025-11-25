C_STYLE_HEADER_EXTENSIONS = {
    # C / C++
    ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx",
    # Java family
    ".java", ".kt", ".kts", ".scala", ".groovy", ".pde",
    # C#
    ".cs",
    # Obj-C
    ".m", ".mm",
    # Web / scripting
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".as", ".php",
    # Other languages
    ".go", ".rs", ".swift", ".hx",
    # Styles
    ".css", ".scss", ".sass",
}

XML_STYLE_HEADER_EXTENSIONS = {
    # Generic XML / HTML
    ".xml", ".html", ".htm", ".xhtml",
    # Stylesheets / schemas / web service defs
    ".xsl", ".xslt", ".xsd", ".wsdl",
    # Feeds
    ".rss", ".atom",
    # Vector / GIS formats
    ".svg", ".kml", ".gml",
    # .NET / MSBuild project & config files (all XML under the hood)
    ".csproj", ".vbproj", ".fsproj", ".props", ".targets", ".resx", ".config", ".nuspec", ".vsixmanifest",
}

PYTHON_STYLE_HEADER_EXTENSIONS = {
    # Python
    ".py", ".pyw",
    # Shell / Unix scripts
    ".sh", ".bash", ".zsh", ".ksh",
    # Other scripting languages
    ".rb",   # Ruby
    ".pl",   # Perl script
    ".pm",   # Perl module
    ".r", ".R",  # R
    ".jl",  # Julia
    # PowerShell
    ".ps1", ".psm1", ".psd1",
    # Config / data formats
    ".yml", ".yaml",
    ".toml",
    ".env",
    ".ini", ".cfg",
    ".mk",   # Make-style include files
}

# Some important files that don't really have an extension but still use `#`
PYTHON_STYLE_HEADER_BASENAMES = {
    "Makefile",
    "makefile",
    "GNUmakefile",
    "Dockerfile",
}

CSV_STYLE_HEADER_EXTENSIONS = {
    ".csv",  # comma-separated
    ".tsv",  # tab-separated
    ".tab",  # tab-separated
    ".psv",  # pipe-separated
    ".txt",  # often used for delimited text
}

TXT_STYLE_HEADER_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".adoc",      # AsciiDoc
    ".log",
    ".nfo",
}

TXT_STYLE_HEADER_BASENAMES = {
    "README",
    "README.txt",
    "LICENSE",
    "LICENSE.txt",
    "COPYING",
    "NOTICE",
}

SH_STYLE_HEADER_EXTENSIONS = {
    ".sh",
    ".bash",
    ".zsh",
    ".ksh",
    ".dash",
    ".ash",
    ".bats",   # bash automated testing system
}

SH_STYLE_HEADER_BASENAMES = {
    "bashrc",
    ".bashrc",
    ".bash_profile",
    "zshrc",
    ".zshrc",
    "profile",
    ".profile",
}