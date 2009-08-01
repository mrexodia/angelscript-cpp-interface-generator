import os
import sys

outfilename = 'output'

template_h = """#ifndef %(header_guard)s
#define %(header_guard)s

#include "angelscript.h"

%(includefiles)s
void registerObjects(AngelScript::asIScriptEngine *engine);

#endif //%(header_guard)s
"""

template_cpp = """#include "output.h"

void registerObjects(AngelScript::asIScriptEngine *engine)
{
%(regs)s
}
"""

def generateHeader(headerfiles):
	global outfilename
	outfile = '%s.h' % outfilename 
	inclf = []
	for file in headerfiles:
		inclf.append('#include "%s"\n'%file.strip())
	content = template_h % {'header_guard':'AS_INTERFACE_H_', 'includefiles':(''.join(inclf))}
	f = open(outfile, 'w')
	f.write(content)
	f.close()
	
def generateCppFile(regs):
	global outfilename
	outfile = '%s.cpp' % outfilename
	# add tabs
	lines = []
	for line in regs.split('\n'):
		lines.append('\t%s\n'%line)
	regs = ''.join(lines)
	content = template_cpp % {'regs':regs}	
	f = open(outfile, 'w')
	f.write(content)
	f.close()


if len(sys.argv) < 2:
	print "usage: %s file1.h file2.h ..." % os.path.basename(sys.argv[0])
	sys.exit(1)

# append the pyctags to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyctags'))
from pyctags import exuberant_ctags, ctags_file
from pyctags.harvesters import kind_harvester

# construct ctags executable path
ctags_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ctags.exe')

files = sys.argv[1:]
newfiles = []
for file in files:
	if os.path.isdir(file):
		for file2 in os.listdir(file):
			fn = os.path.join(file, file2)
			if os.path.isfile(fn):
				newfiles.append(fn)
	elif os.path.isfile(file):
		newfiles.append(file)
files = newfiles

print newfiles

# load files into memory
filecontent = {}
for file in files:
	f = open(file, 'r')
	filecontent[file] = f.readlines()
	f.close()

# create the class
ctags = exuberant_ctags(tag_program=ctags_path, files=files)

# you can generate a ctags_file instance right away
# ctags_file is what parses lines from the generator or a 
# tags file and creates a list of ctags_entry instances
tag_file = ctags.generate_object()

# override the default run parameters for exuberant ctags, so we get full kind names, say
tag_file = ctags.generate_object(generator_options={'--fields' : '+afmikKlnsStz', '-F' : None, '--c++-kinds':'+cegfmnpstv '})

#print tag_file.tags

USE_NAMESPACE_CLASSNAMES = False

harvester = kind_harvester()
harvester.process_tag_list(tag_file.tags)
kinds = harvester.get_data()
#print kinds
lastClass = ''

typemap = {
	'unsigned int' : 'uint',
	'unsigned char' : 'uint8',
	'unsigned long' : 'uint16',
	# 64?
	
	'char' : 'int8',
	'int' : 'int32',
	'long long' : 'int64',
	'Real' : 'float',
	'void' : '',
}

behaviormap = {
	'Constructor' : 'asBEHAVE_CONSTRUCT', 
	'Destructor' : 'asBEHAVE_DESTRUCT', 
	'Factory' : 'asBEHAVE_FACTORY', 
	'AddRef' : 'asBEHAVE_ADDREF', 
	'Release' : 'asBEHAVE_RELEASE', 
	'Explicit value cast operator' : 'asBEHAVE_VALUE_CAST', 
	'Implicit value cast operator' : 'asBEHAVE_IMPLICIT_VALUE_CAST', 
	'operator []' : 'asBEHAVE_INDEX', 
	'operator -' : 'asBEHAVE_NEGATE', 
	'operator =' : 'asBEHAVE_ASSIGNMENT', 
	'operator +=' : 'asBEHAVE_ADD_ASSIGN', 
	'operator -=' : 'asBEHAVE_SUB_ASSIGN', 
	'operator *=' : 'asBEHAVE_MUL_ASSIGN', 
	'operator /=' : 'asBEHAVE_DIV_ASSIGN', 
	#'operator =' : 'asBEHAVE_MOD_ASSIGN', 
	'operator |=' : 'asBEHAVE_OR_ASSIGN', 
	'operator &=' : 'asBEHAVE_AND_ASSIGN', 
	'operator ^=' : 'asBEHAVE_XOR_ASSIGN', 
	'operator <<=' : 'asBEHAVE_SLL_ASSIGN', 
	'operator >>=' : 'asBEHAVE_SRL_ASSIGN', 
	'operator >>>=' : 'asBEHAVE_SRA_ASSIGN', 
	'operator +' : 'asBEHAVE_ADD', 
	'operator -' : 'asBEHAVE_SUBTRACT', 
	'operator *' : 'asBEHAVE_MULTIPLY', 
	'operator /' : 'asBEHAVE_DIVIDE', 
	'operator %' : 'asBEHAVE_MODULO', 
	'operator ==' : 'asBEHAVE_EQUAL', 
	'operator !=' : 'asBEHAVE_NOTEQUAL', 
	'operator <' : 'asBEHAVE_LESSTHAN', 
	'operator >' : 'asBEHAVE_GREATERTHAN', 
	'operator <=' : 'asBEHAVE_LEQUAL', 
	'operator >=' : 'asBEHAVE_GEQUAL', 
	'operator |' : 'asBEHAVE_BIT_OR', 
	'operator &' : 'asBEHAVE_BIT_AND', 
	'operator ^' : 'asBEHAVE_BIT_XOR', 
	'operator <<' : 'asBEHAVE_BIT_SLL', 
	'operator >>' : 'asBEHAVE_BIT_SRL', 
	'operator >>>' : 'asBEHAVE_BIT_SRA', 
	'Explicit reference cast operator' : 'asBEHAVE_REF_CAST', 
	'Implicit reference cast operator' : 'asBEHAVE_IMPLICIT_REF_CAST', 
	'Get reference count' : 'asBEHAVE_GETREFCOUNT', 
	'Set GC flag' : 'asBEHAVE_SETGCFLAG', 
	'Get GC flag' : 'asBEHAVE_GETGCFLAG', 
	'Enumerate held references' : 'asBEHAVE_ENUMREFS', 
	'Release all references' : 'asBEHAVE_RELEASEREFS', 
}

result = ""

# collect classes
classmap = {}
for entry_type in kinds.keys():
	if entry_type != 'class':
		continue
	for entry in kinds[entry_type]:
		ns = ''
		if 'namespace' in entry.extensions.keys():
			ns = entry.extensions['namespace'] + '_'
		#classmap[entry.name] = ns + entry.name + 'Class'
		if USE_NAMESPACE_CLASSNAMES:
			classmap[entry.name] = ns + entry.name
		else:
			classmap[entry.name] = entry.name
			

def getShortClassName(clsname):
	if USE_NAMESPACE_CLASSNAMES:
		return clsname.replace('::', '_')
	else:
		return clsname.split('::')[-1]

def replaceClassnames(str):
	global classmap
	for entry in classmap.keys():
		str = str.replace(entry, classmap[entry])
	return str

def processSignatureASDecl(sig):
	global typemap
	sig = sig.replace('const', '')
	sig = sig.strip(' ()')
	
	entries = sig.split(',')
	new_entries = []
	for entry in entries:
		entry = entry.strip()
		# by now we should have the variable name and the type
		byRef = False
		#print '>>>>', entry
		if entry.find('&') != -1:
			byRef = True
		entry = entry.replace('&', '')
		vartype = entry.strip().split(' ')[0]
		for tm in typemap.keys():
			if vartype[:len(tm)] == tm:
				vartype = vartype.replace(tm, typemap[tm])
		newentry = ''
		if byRef:
			newentry = '%(vartype)s &in' % {'vartype':vartype}
		else:
			newentry = '%(vartype)s' % {'vartype':vartype}
		#print '####', newentry
		new_entries.append(newentry)
	return '(%s)' % ', '.join(new_entries)

def handleKind(entry_type):
  result=''
  for entry in kinds[entry_type]:
	line = filecontent[entry.file][entry.line_number-1]
	
	#print entry.name
	#for k in entry.extensions:
	#    print k,'\t\t', entry.extensions[k]
	
	if entry.name.find('operator') == -1:
		type = line.strip()[:line.strip().find(entry.name)].strip()
	else:
		entryname = ''.join(entry.name.split())
		type = line.strip()[:line.strip().find(entryname)].strip()
	#print entry.name, type
	static = False
	if type.find('static') != -1:
		type = type.replace('static', '').strip()
		static=True
	# try to match known handles
	for tm in typemap.keys():
		if type[:len(tm)] == tm:
			type = type.replace(tm, typemap[tm])
	# replace pointers
	if len(type) > 0 and type[-1] == '*':
		type = type[:-1]+'@'
	if type.find('::') != -1:
		type=type.replace('::', '_') #+'Class'
	type=type.replace('inline', '').strip()
	type=type.replace('explicit', '').strip()
	type= replaceClassnames(type)
	if type.find(',') != -1:
		args = type.split(',')
		type = args[0].split(' ')[0] + args[-1]
	#print type
	if entry_type == 'member':
		if entry.extensions['access'] != 'public':
			continue
		clsname = ''
		if 'class' in entry.extensions.keys():
			clsname = entry.extensions['class']
		#result += "//" + line.strip() + "\n"
		if not static:
			result += "r = engine->RegisterObjectProperty(\"%(shortclassname)s\", \"%(type)s %(name)s\", offsetof(%(classname)s, %(name)s)); assert(r>=0);\n" % \
					{
						'type':type,
						'classname':clsname, 
						'shortclassname':getShortClassName(clsname), 
						'name':entry.name
					}
		else:
			clsstr = entry.name
			if clsname != '':
				clsstr = clsname+'::'+entry.name
			result += "r = engine->RegisterGlobalProperty(\"%(type)s %(name)s\", &%(clsstr)s); assert(r>=0);\n" % \
					{
						'type':type,
						'clsstr':clsstr, 
						'shortclassname':getShortClassName(clsname),
						'name':entry.name
					}
		#result += "\n"
			

	elif entry_type in ['function', 'prototype']:
		if 'access' in entry.extensions.keys() and entry.extensions['access'] != 'public':
			continue
		lname = entry.name
		if len(type) > 0 and type[-1] != '@':
			lname = ' '+lname
		elif len(type) > 0 and type[-1] == '@':
			type = type[:-1]
			lname = ' @' + lname
		#result += "//" + line.strip() + "\n"
		if not entry.name in behaviormap.keys():
			# normal function
			
			if entry.name == getShortClassName(entry.extensions['class']) or entry.name.find('~') != -1:
				result += "// constructor/destructor: (FIX MANUALLY!) \n//"
			
			type = type.replace('const', '').strip()

			# replace type with known type
			for tm in typemap.keys():
				if type[:len(tm)] == tm:
					type = type.replace(tm, typemap[tm])

			if type.strip() == '':
				type = 'void '
				
			#print '1>>',entry.extensions['signature']
			as_signature = processSignatureASDecl(entry.extensions['signature'])
			result += "r = engine->RegisterObjectMethod(\"%(shortclassname)s\", \"%(type)s%(name)s%(signature)s\", asMETHODPR(%(classname)s,%(name)s, %(signature)s, %(type)s), asCALL_THISCALL); assert(r>=0);\n" % \
					{
						'type':type,
						'classname':entry.extensions['class'], 
						'shortclassname':getShortClassName(entry.extensions['class']),
						'name':lname, 
						'signature':as_signature
					}
			#result += "\n"
		else:
			# behavior
			behaviortype = behaviormap[entry.name]
			lname = lname.replace(entry.name, 'f')
			#print lname
			#print type
			type = type[0:type.find('operator')].strip()
			# rearrange the & sign
			if type[-1] == '&':
				type = type[:-1]
				lname = ' &' + lname.strip()
			result += "r = engine->RegisterObjectBehaviour(\"%(shortclassname)s\", %(behaviortype)s, \"%(type)s%(name)s%(signature)s\", asMETHODPR(%(classname)s,%(realname)s, %(signature)s, %(type)s), asCALL_THISCALL); assert(r>=0);\n" % \
					{
						'behaviortype':behaviortype,
						'type':type,
						'classname':entry.extensions['class'], 
						'shortclassname':getShortClassName(entry.extensions['class']),
						'name':lname, 
						'realname':entry.name, 
						'signature':processSignatureASDecl(entry.extensions['signature'])
					}
			#result += "\n"
			
		#print entry.name, '\t\t', entry.extensions['signature']
	elif entry_type == 'class':
		lastClass = entry.name
		result += "r = engine->RegisterObjectType(\"%(classname)s\", sizeof(%(classname)s), asOBJ_REF); assert(r>=0);\n" % {'classname': entry.name}
  return result

	
# this sorts the result a bit depending on the type
result = ''
entry_types = ['class', 'member', 'function', 'prototype']
for entry_type in entry_types:
  if entry_type in kinds.keys():
    res = handleKind(entry_type)
    if res != '':
      result += "/// %s\n" % str(entry_type)
      result += res

generateHeader(files)
generateCppFile(result)




print "processed %d tags. output file %s{.cpp,.h} written" % (len(tag_file.tags), outfilename)
