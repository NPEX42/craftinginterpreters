#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import codecs
import glob
import os
import posixpath
import re
import subprocess
import sys
import time
import urllib
from http.server import HTTPServer, SimpleHTTPRequestHandler

import jinja2
import markdown

import sections

GRAY = '\033[1;30m'
GREEN = '\033[32m'
RED = '\033[31m'
DEFAULT = '\033[0m'
PINK = '\033[91m'
YELLOW = '\033[33m'

CODE_BEFORE_PATTERN = re.compile(r'(\d+) \((\d+) before\)')
CODE_AFTER_PATTERN = re.compile(r'(\d+) \((\d+) after\)')
CODE_AROUND_PATTERN = re.compile(r'(\d+) \((\d+) before, (\d+) after\)')

TOC = [
  {
    'name': '',
    'chapters': [
      {
        'name': 'Crafting Interpreters',
        'topics': [],
      },
      {
        'name': 'Table of Contents',
        'topics': [],
      }
    ],
  },
  {
    'name': 'Welcome',
    'chapters': [
      {
        'name': 'Introduction',
        'topics': [
          'Why learn programming languages?',
          'How this book is organized'
        ],
        'design_note': "What's in a Name?"
      },
      {
        'name': 'A Map of the Territory',
        'topics': [
          'Interpreters and compilers', 'Phases of a compiler',
          'Transpilers', 'Just-in-time compilation'
        ],
      },
      {
        'name': 'The Lox Language',
        'topics': [
          'Dynamic typing', 'Automatic memory management', 'Built-in types',
          'Expressions', 'Statements', 'Object-orientation', 'Prototypes'
        ],
        'design_note': "Statements and Expressions"
      }
    ]
  },
  {
    'name': 'A Tree-Walk Interpreter in Java',
    'chapters': [
      {
        'name': 'Scanning',
        'topics': [
          'Tokens', 'Token types', 'Lexical analysis', 'Regular languages',
          'Lookahead', 'Reserved words', 'Error reporting'
        ],
        'done': False,
      },
      {
        'name': 'Representing Code',
        'topics': [
          'Abstract syntax trees', 'Expression trees', 'Generating AST classes',
          'The Visitor pattern', 'Pretty printing'
        ],
        'done': False,
      },
      {
        'name': 'Parsing Expressions',
        'topics': [
          'Expression nodes', 'Recursive descent', 'Precedence',
          'Associativity', 'Primary expressions', 'Syntax errors'
        ],
        'done': False,
      },
      {
        'name': 'Evaluating Expressions',
        'topics': [
          'The Interpreter pattern', 'Tree-walk interpretation',
          'Subexpressions', 'Runtime errors', 'Type checking', 'Truthiness'
        ],
        'done': False,
      },
      {
        'name': 'Statements and State',
        'topics': [
          'Statement nodes', 'Blocks', 'Expression statements', 'Variables',
          'Assignment', 'Lexical scope', 'Environments'
        ],
        'done': False,
      },
      {
        'name': 'Control Flow',
        'topics': [
          'If statements', 'While statements', 'For statements', 'Desugaring',
          'Logical operators', 'Short-circuit evaluation'
        ],
        'done': False,
      },
      {
        'name': 'Functions',
        'topics': [
          'Function declarations', 'Formal parameters', 'Call expressions',
          'Arguments', 'Return statements', 'Function objects', 'Closures',
          'Arity', 'Native functions'
        ],
        'done': False,
      },
      {
        'name': 'Resolving and Binding',
        'topics': ['Name resolution', 'Early binding', 'Static errors'],
        'done': False,
      },
      {
        'name': 'Classes',
        'topics': [
          'Class declarations', 'Fields', 'Properties',
          'Get and set expressions', 'Constructors', 'Initializers', 'this',
          'Method references'
        ],
        'done': False,
      },
      {
        'name': 'Inheritance',
        'topics': ['Superclasses', 'Overriding', 'Calling superclass methods'],
        'done': False,
      }
    ]
  },
  {
    'name': 'A Bytecode Interpreter in C',
    'chapters': [
      {
        'name': 'Chunks of Bytecode',
        'topics': [
          'Allocation', 'Dynamic arrays', 'Code chunks', 'Constant tables',
          'Instruction arguments', 'Disassembly'
        ],
        'done': False,
      },
      {
        'name': 'A Virtual Machine',
        'topics': [
          'Bytecode instructions', 'The stack', 'Instruction pointer',
          'Loading constants', 'Arithmetic instructions', 'Interpreter loop',
          'Instruction dispatch'
        ],
        'done': False,
      },
      {
        'name': 'Scanning on Demand',
        'topics': [
          'Reading files', 'Token values', 'Source pointers', 'LL(k) grammars'
        ],
        'done': False,
      },
      {
        'name': 'Compiling Expressions',
        'topics': [
          'Pratt parsers', 'Binary operators', 'Unary operators', 'Precedence',
          'Single-pass compilation', 'Code generation'
        ],
        'done': False,
      },
      {
        'name': 'Types of Values',
        'topics': [
          'Tagged unions', 'Boolean values', 'nil',
          'Comparison and equality operators', 'Not operator', 'Runtime errors'
        ],
        'done': False,
      },
      {
        'name': 'Strings',
        'topics': [
          'Objects', 'Reference types', 'Heap tracing', 'Concatenation',
          'Polymorphism'
        ],
        'done': False,
      },
      {
        'name': 'Hash Tables',
        'topics': [
          'Hash functions', 'FNV-1a string hashing', 'Linear probing',
          'Rehashing', 'Reference equality', 'String interning'
        ],
        'done': False,
      },
      {
        'name': 'Global Variables',
        'topics': [
          'Statements', 'Variable declaration', 'Assignment',
          'Global variables table'
        ],
        'done': False,
      },
      {
        'name': 'Local Variables',
        'topics': [
          'Blocks', 'Scope depth', 'Stack variables', 'Name resolution',
          'Byte argument instructions'
        ],
        'done': False,
      },
      {
        'name': 'Jumping Forward and Back',
        'topics': [
          'Jump instructions', 'Conditional jumps', 'Control flow statements',
          'Short-circuiting', 'Backpatching'
        ],
        'done': False,
      },
      {
        'name': 'Calls and Functions',
        'topics': [
          'Calling convention', 'Arguments', 'Call instructions',
          'Native functions', 'Function declarations', 'Parameters',
          'Return statements', 'Function objects', 'Call frames',
          'Stack overflow'
        ],
        'done': False,
      },
      {
        'name': 'Closures',
        'topics': [
          'Upvalues', 'Resolving enclosing locals', 'Closure flattening',
          'Capturing variables', 'Closing upvalues'
        ],
        'done': False,
      },
      {
        'name': 'Garbage Collection',
        'topics': [
          'Roots', 'Stress testing', 'Mark-sweep collection', 'Tracing',
          'Tri-color marking', 'Weak references', 'Heap growth'
        ],
        'done': False,
      },
      {
        'name': 'Classes and Instances',
        'topics': [
          'Property expressions', 'Class declarations', 'Instances', 'Fields',
          'Undefined fields'
        ],
        'done': False,
      },
      {
        'name': 'Methods and Initializers',
        'topics': [
          'Invocation expressions', 'This', 'Method declarations',
          'Initializers', 'Bound methods'
        ],
        'done': False,
      },
      {
        'name': 'Superclasses',
        'topics': [
          'Method inheritance', 'Super invocations'
        ],
        'done': False,
      },
      {
        'name': 'Optimization',
        'topics': [
          'Benchmarking', 'Hash code masking', 'NaN tagging'
        ],
        'done': False,
      }
    ]
  },
]


def flatten_pages():
  """Flatten the tree of parts and chapters to a single linear list of pages."""
  pages = []
  for part in TOC:
    # There are no part pages for the front- and backmatter.
    if part['name']:
      pages.append(part['name'])

    for chapter in part['chapters']:
      pages.append(chapter['name'])

  return pages

PAGES = flatten_pages()


def roman(n):
  """Convert n to roman numerals."""
  if n <= 3:
    return "I" * n
  elif n == 4:
    return "IV"
  elif n < 10:
    return "V" + "I" * (n - 5)
  else:
    raise "Can't convert " + str(n) + " to Roman."

def number_chapters():
  """Determine the part or chapter numbers for each part or chapter."""
  numbers = {}
  part_num = 1
  chapter_num = 1
  in_matter = False
  for part in TOC:
    # Front- and backmatter have no names, pages, or numbers.
    in_matter = part['name'] == ''
    if not in_matter:
      numbers[part['name']] = roman(part_num)
      part_num += 1

    for chapter in part['chapters']:
      if in_matter:
        # Front- and backmatter chapters are not numbered.
        numbers[chapter['name']] = ''
      else:
        numbers[chapter['name']] = str(chapter_num)
        chapter_num += 1

  return numbers

NUMBERS = number_chapters()


num_chapters = 0
empty_chapters = 0
total_words = 0

source_code = None

class RootedHTTPServer(HTTPServer):
  """Simple server that resolves paths relative to a given directory.

  From: http://louistiao.me/posts/python-simplehttpserver-recipe-serve-specific-directory/
  """
  def __init__(self, base_path, *args, **kwargs):
    HTTPServer.__init__(self, *args, **kwargs)
    self.RequestHandlerClass.base_path = base_path


class RootedHTTPRequestHandler(SimpleHTTPRequestHandler):
  """Simple handler that resolves paths relative to a given directory.

  From: http://louistiao.me/posts/python-simplehttpserver-recipe-serve-specific-directory/
  """
  def translate_path(self, path):
    # Refresh files that are being requested.
    if path.endswith(".html"):
      format_files(True, path.replace(".html", "").replace("/", ""))
    if path.endswith(".css"):
      build_sass(True)

    path = posixpath.normpath(urllib.parse.unquote(path))
    words = path.split('/')
    words = filter(None, words)
    path = self.base_path
    for word in words:
      drive, word = os.path.splitdrive(word)
      head, word = os.path.split(word)
      if word in (os.curdir, os.pardir):
        continue
      path = os.path.join(path, word)
    return path


def title_to_file(title):
  '''Given a title like "Hash Tables", converts it to the corresponding file
     name like "hash-tables".'''
  if title == "Crafting Interpreters":
    return "index"
  if title == "Table of Contents":
    return "contents"

  title = title.lower().replace(" ", "-")
  title = re.sub(r'[,.?!:/"]', '', title)
  return title


def adjacent_page(title, offset):
  '''Generate template data to link to the previous or next page.'''
  page_index = PAGES.index(title) + offset
  if page_index < 0 or page_index >= len(PAGES): return None

  return PAGES[page_index]


def pretty(text):
  '''Use nicer HTML entities and special characters.'''
  text = text.replace(" -- ", "&#8202;&mdash;&#8202;")
  text = text.replace(" --\n", "&#8202;&mdash;&#8202;")
  text = text.replace("à", "&agrave;")
  text = text.replace("ï", "&iuml;")
  text = text.replace("ø", "&oslash;")
  text = text.replace("æ", "&aelig;")
  return text


def look_up_chapters(title):
  """If [title] is the title of a part, returns a list of pairs of chapter
  numbers and names."""
  chapters = []
  for part in TOC:
    if title == part['name']:
      chapter_number = int(NUMBERS[part['chapters'][0]['name']])
      for chapter in part['chapters']:
        chapters.append([chapter_number, chapter['name']])
        chapter_number += 1
      break

  return chapters


def format_code(language, lines):
  markup = '```{}\n'.format(language)

  # Hack. Markdown seems to discard leading and trailing newlines, so we'll
  # add them back ourselves.
  leading_newlines = 0
  while lines and lines[0].strip() == '':
    lines = lines[1:]
    leading_newlines += 1

  trailing_newlines = 0
  while lines and lines[-1].strip() == '':
    lines = lines[:-1]
    trailing_newlines += 1

  for line in lines:
    markup += line + '\n'

  markup += '```'

  html = markdown.markdown(markup, ['extra', 'codehilite'])

  if leading_newlines > 0:
    html = html.replace('<pre>', '<pre>' + ('<br>' * leading_newlines))

  if trailing_newlines > 0:
    html = html.replace('</pre>', ('<br>' * trailing_newlines) + '</pre>')

  # Strip off the div wrapper. We just want the <pre>.
  html = html.replace('<div class="codehilite">', '')
  html = html.replace('</div>', '')
  return html


def include_section(sections, arg, contents):
  number = None
  before_lines = 0
  after_lines = 0

  match = CODE_BEFORE_PATTERN.match(arg)
  if match:
    number = int(match.group(1))
    before_lines = int(match.group(2))

  match = CODE_AFTER_PATTERN.match(arg)
  if match:
    number = int(match.group(1))
    after_lines = int(match.group(2))

  match = CODE_AROUND_PATTERN.match(arg)
  if match:
    number = int(match.group(1))
    before_lines = int(match.group(2))
    after_lines = int(match.group(3))

  if not number:
    number = int(arg)

  if number not in sections:
    contents = "**ERROR: Undefined section {}**\n\n".format(number) + contents
    contents += "**ERROR: Missing section {}**\n".format(number)
    return contents

  if sections[number] == False:
    contents = "**ERROR: Reused section {}**\n\n".format(number) + contents
    contents += "**ERROR: Reused section {}**\n".format(number)
    return contents

  section = sections[number]

  # Consume it.
  sections[number] = False

  # TODO: Show indentation in snippets somehow.

  contents += '<div class="codehilite">'

  if before_lines > 0:
    before = format_code(section.file.language(),
        section.context_before[-before_lines:])
    before = before.replace('<pre>', '<pre class="insert-before">')
    contents += before

  where = '<em>{}</em>'.format(section.file.nice_path())

  if section.location():
    where += '<br>\n{}'.format(section.location())

  if section.removed and section.added:
    where += '<br>\nreplace {} line{}'.format(
        len(section.removed), '' if len(section.removed) == 1 else 's')
  contents += '<div class="source-file">{}</div>\n'.format(where)

  if section.removed and not section.added:
    removed = format_code(section.file.language(), section.removed)
    removed = removed.replace('<pre>', '<pre class="delete">')
    contents += removed

  if section.added:
    added = format_code(section.file.language(), section.added)
    if before_lines > 0 or after_lines > 0:
      added = added.replace('<pre>', '<pre class="insert">')
    contents += added

  if after_lines > 0:
    after = format_code(section.file.language(),
        section.context_after[:after_lines])
    after = after.replace('<pre>', '<pre class="insert-after">')
    contents += after

  contents += '</div>'

  return contents


def format_file(path, skip_up_to_date, dependencies_mod):
  basename = os.path.basename(path)
  basename = basename.split('.')[0]

  output_path = "site/" + basename + ".html"

  # See if the HTML is up to date.
  if skip_up_to_date:
    source_mod = max(os.path.getmtime(path), dependencies_mod)
    dest_mod = os.path.getmtime(output_path)

    if source_mod < dest_mod:
      return

  title = ''
  title_html = ''
  part = None
  template_file = 'page'

  sections = []
  header_index = 0
  subheader_index = 0
  has_challenges = False
  design_note = None
  code_sections = None

  # Read the markdown file and preprocess it.
  contents = ''
  with open(path, 'r') as input:
    # Read each line, preprocessing the special codes.
    for line in input:
      stripped = line.lstrip()
      indentation = line[:len(line) - len(stripped)]

      if stripped.startswith('^'):
        command,_,arg = stripped.rstrip('\n').lstrip('^').partition(' ')
        arg = arg.strip()

        if command == 'title':
          title = arg
          title_html = title

          # Remove any discretionary hyphens from the title.
          title = title.replace('&shy;', '')

          # Load the code snippets now that we know the title.
          code_sections = source_code.find_all(title)
        elif command == 'part':
          part = arg
        elif command == 'template':
          template_file = arg
        elif command == 'code':
          contents = include_section(code_sections, arg, contents)
        else:
          raise Exception('Unknown command "^{} {}"'.format(command, arg))

      elif stripped.startswith('## Challenges'):
        has_challenges = True
        contents += '<h2><a href="#challenges" name="challenges">Challenges</a></h2>\n'

      elif stripped.startswith('## Design Note:'):
        has_design_note = True
        design_note = stripped[len('## Design Note:') + 1:]
        contents += '<h2><a href="#design-note" name="design-note">Design Note: {}</a></h2>\n'.format(design_note)

      elif stripped.startswith('#') and not stripped.startswith('####'):
        # Build the section navigation from the headers.
        index = stripped.find(" ")
        header_type = stripped[:index]
        header = pretty(stripped[index:].strip())
        anchor = title_to_file(header)
        anchor = re.sub(r'[.?!:/"]', '', anchor)

        # Add an anchor to the header.
        contents += indentation + header_type

        if len(header_type) == 2:
          header_index += 1
          subheader_index = 0
          number = '{0}&#8202;.&#8202;{1}'.format(NUMBERS[title], header_index)
        elif len(header_type) == 3:
          subheader_index += 1
          number = '{0}&#8202;.&#8202;{1}&#8202;.&#8202;{2}'.format(NUMBERS[title], header_index, subheader_index)

        header_line = '<a href="#{0}" name="{0}"><small>{1}</small> {2}</a>\n'.format(anchor, number, header)
        contents += header_line

        # Build the section navigation.
        if len(header_type) == 2:
          sections.append([header_index, header])

      else:
        contents += pretty(line)

  # Validate that every section for the chapter is included.
  # TODO: Hack. If the chapter only has one section, it means I haven't written
  # it and sliced up its code yet. Just ignore it.
  if len(code_sections) > 1:
    for number, section in code_sections.items():
      if section != False:
        contents = "**ERROR: Unused section {}**\n\n".format(number) + contents

  chapters = look_up_chapters(title)

  # Allow processing markdown inside some tags.
  contents = contents.replace('<aside', '<aside markdown="1"')
  contents = contents.replace('<div class="challenges">', '<div class="challenges" markdown="1">')
  contents = contents.replace('<div class="design-note">', '<div class="design-note" markdown="1">')
  body = markdown.markdown(contents, ['extra', 'codehilite', 'smarty'])

  data = {
    'title': title,
    'part': part,
    'body': body,
    'sections': sections,
    'chapters': chapters,
    'design_note': design_note,
    'has_challenges': has_challenges,
    'number': NUMBERS[title],
    'prev': adjacent_page(title, -1),
    'next': adjacent_page(title, 1),
    'toc': TOC
  }

  template = environment.get_template(template_file + '.html')
  output = template.render(data)

  # Write the output.
  with codecs.open(output_path, "w", encoding="utf-8") as out:
    out.write(output)

  global total_words
  global num_chapters
  global empty_chapters

  word_count = len(contents.split(None))
  num = NUMBERS[title]
  if num:
    num += '. '

  # Non-chapter pages aren't counted like regular chapters.
  if part:
    num_chapters += 1
    if word_count < 50:
      empty_chapters += 1
      print("    {}{}{}{}".format(GRAY, num, title, DEFAULT))
    elif word_count < 2000:
      empty_chapters += 1
      print("  {}-{} {}{} ({} words)".format(
        YELLOW, DEFAULT, num, title, word_count))
    else:
      total_words += word_count
      print("  {}✓{} {}{} ({} words)".format(
        GREEN, DEFAULT, num, title, word_count))
  elif title in ["Crafting Interpreters", "Table of Contents"]:
    print("{}•{} {}{}".format(
      GREEN, DEFAULT, num, title))
  else:
    if word_count < 50:
      print("  {}{}{}{}".format(GRAY, num, title, DEFAULT))
    else:
      print("{}✓{} {}{} ({} words)".format(
        GREEN, DEFAULT, num, title, word_count))


def latest_mod(glob_pattern):
  ''' Returns the mod time of the most recently modified file match
      [glob_pattern].
  '''
  latest = None
  for file in glob.iglob(glob_pattern):
    file_mod = os.path.getmtime(file)
    if not latest: latest = file_mod
    latest = max(latest, file_mod)
  return latest


last_code_load_time = None

def format_files(skip_up_to_date, one_file=None):
  '''Process each markdown file.'''

  code_mod = max(
      latest_mod("c/*.c"),
      latest_mod("c/*.h"),
      latest_mod("java/com/craftinginterpreters/tool/*.java"),
      latest_mod("java/com/craftinginterpreters/lox/*.java"))

  # Reload the source sections if the code was changed.
  global source_code
  global last_code_load_time
  if not last_code_load_time or code_mod > last_code_load_time:
    source_code = sections.load()
    last_code_load_time = time.time()

  # See if any of the templates were modified. If so, all pages will be rebuilt.
  templates_mod = latest_mod("asset/template/*.html")

  for page in PAGES:
    page_file = title_to_file(page)
    if one_file == None or page_file == one_file:
      file = os.path.join('book', page_file + '.md')
      format_file(file, skip_up_to_date, max(code_mod, templates_mod))


def build_sass(skip_up_to_date):
  '''Process each SASS file.'''
  imports_mod = None
  for source in glob.iglob("asset/sass/*.scss"):
    import_mod = os.path.getmtime(source)
    if not imports_mod: imports_mod = import_mod
    imports_mod = max(imports_mod, import_mod)

  for source in glob.iglob("asset/*.scss"):
    dest = "site/" + os.path.basename(source).split(".")[0] + ".css"

    if skip_up_to_date:
      source_mod = max(os.path.getmtime(source), imports_mod)
      dest_mod = os.path.getmtime(dest)
      if source_mod < dest_mod:
        continue

    subprocess.call(['sass', source, dest])
    print("{}•{} {}".format(GREEN, DEFAULT, source))


def run_server():
  port = 8000
  handler = RootedHTTPRequestHandler
  server = RootedHTTPServer("site", ('', port), handler)

  print('Serving at port', port)
  server.serve_forever()


environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader('asset/template'),
    lstrip_blocks=True,
    trim_blocks=True)

environment.filters['file'] = title_to_file

if len(sys.argv) == 2 and sys.argv[1] == "--watch":
  run_server()
  while True:
    format_files(True)
    build_sass(True)
    time.sleep(0.3)
if len(sys.argv) == 2 and sys.argv[1] == "--serve":
  format_files(True)
  run_server()
else:
  format_files(False)
  build_sass(False)

  average_word_count = total_words // (num_chapters - empty_chapters)
  estimated_word_count = total_words + (empty_chapters * average_word_count)
  percent_finished = total_words * 100 // estimated_word_count

  print("{}/~{} words ({}%)".format(
    total_words, estimated_word_count, percent_finished))
