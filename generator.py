#!/bin/env python
import os
import sys
import platform

# append the pyctags to the path
sys.path.append(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyctags'))
from pyctags import exuberant_ctags, ctags_file
from pyctags.harvesters import kind_harvester

# main class:


class AngelScriptInterfaceGenerator:
    # some class variables
    use_namespace_names = False

    template_h = """#ifndef %(header_guard)s
#define %(header_guard)s

#include "angelscript.h"

%(includefiles)s
void RegisterObjects(AngelScript::asIScriptEngine* engine);

#endif //%(header_guard)s
"""

    template_cpp = """#include "output.h"

#ifdef _DEBUG
#define VERIFY(x) assert((x) >= 0)
#else
#define VERIFY(x) x
#endif

void RegisterObjects(AngelScript::asIScriptEngine* engine)
{
%(regs)s
}
"""

    typemap = {
        'unsigned char': 'uint8',
        'unsigned short': 'uint16',
        'unsigned int': 'uint',
        'unsigned long': 'uint',
        'unsigned long long': 'uint64',

        'char': 'int8',
        'short': 'int16',
        'long': 'int',
        'long long': 'int64',
        'void': '',

        # custom type definitions
        'SCRIPT_EXPORT': ''
    }

    behaviormap = {
        'Constructor': 'asBEHAVE_CONSTRUCT',
        'Destructor': 'asBEHAVE_DESTRUCT',
        'Factory': 'asBEHAVE_FACTORY',
        'AddRef': 'asBEHAVE_ADDREF',
        'Release': 'asBEHAVE_RELEASE',
    }

    calling_convention = 'asCALL_CDECL'

    def __init__(self):
        # construct ctags executable path
        if platform.system() == "Linux":
            # stupid assumption, fix that if needed:
            self.ctags_path = '/usr/bin/ctags'
        elif platform.system() == "Windows":
            self.ctags_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 'ctags.exe')
        else:
            print "you need to fix the generator.py from line 97 on in order to find the ctags executabe!"
            sys.exit(2)

    def saveGenerateHeader(self, filename='output.h'):
        f = open(filename, 'w')
        f.write(self.generateHeader())
        f.close()

    def generateHeader(self):
        inclf = []
        for file in self.files:
            inclf.append('#include "%s"\n' % os.path.basename(file.strip()))
        return self.template_h % {'header_guard': 'AS_INTERFACE_H_', 'includefiles': (''.join(inclf))}

    def saveGenerateCppFile(self, filename='output.cpp'):
        f = open(filename, 'w')
        f.write(self.generateCppFile())
        f.close()

    def generateCppFile(self):
        # add tabs
        lines = []
        regs = self.result
        for line in regs.split('\n'):
            lines.append('\t%s\n' % line)
        regs = ''.join(lines)
        return self.template_cpp % {'regs': regs}

    def getShortClassName(self, clsname):
        if self.use_namespace_names:
            return clsname.replace('::', '_')
        else:
            return clsname.split('::')[-1]

    def replaceClassnames(self, classmap, str):
        for entry in classmap.keys():
            str = str.replace(entry, classmap[entry])
        return str

    def _processSignatureASDecl(self, sig, cpp=False):
        constReturn = False
        sig = sig.strip(' ()')
        if sig[-5:] == "const":
            sig = sig[:-5]
            constReturn = True
        sig = sig.strip(' ()')
        entries = sig.split(',')
        new_entries = []
        for entry in entries:
            # print entries
            entry = entry.strip()
            # by now we should have the variable name and the type
            byRef = False
            # print '>>>>', entry
            if entry.find('&') != -1:
                byRef = True
            entry = entry.replace('&', '')
            vartype = entry.strip().split(' ')[0]
            if vartype == 'const':
                vartype = 'const ' + entry.strip().split(' ')[1]

            for tm in self.typemap.keys():
                if vartype[:len(tm)] == tm:
                    vartype = vartype.replace(tm, self.typemap[tm])
            newentry = ''
            if byRef:
                if cpp:
                    newentry = '%(vartype)s &' % {'vartype': vartype}
                else:
                    newentry = '%(vartype)s &in' % {'vartype': vartype}
            else:
                newentry = '%(vartype)s' % {'vartype': vartype}
            # print '####', newentry
            new_entries.append(newentry)
        if constReturn:
            return '(%s) const' % ', '.join(new_entries)
        else:
            return '(%s)' % ', '.join(new_entries)

    def _handleKind(self, kinds, entry_type):
        result = ''
        for entry in kinds[entry_type]:
            line = self.filecontent[entry.file][entry.line_number - 1]

            # print entry.name
            # for k in entry.extensions:
            #    print k,'\t\t', entry.extensions[k]

            if entry.name.find('operator') == -1:
                type = line.strip()[:line.strip().find(entry.name)].strip()
            else:
                entryname = ''.join(entry.name.split())
                type = line.strip()[:line.strip().find(entryname)].strip()
            # print entry.name, type
            static = False
            if type.find('static') != -1:
                type = type.replace('static', '').strip()
                static = True
            # try to match known handles
            for tm in self.typemap.keys():
                if type[:len(tm)] == tm:
                    type = type.replace(tm, self.typemap[tm])
            # replace pointers
            if len(type) > 0 and type[-1] == '*':
                type = type[:-1] + '@'
            if type.find('::') != -1:
                type = type.replace('::', '_')  # +'Class'
            type = type.replace('inline', '').strip()
            type = type.replace('explicit', '').strip()
            type = self.replaceClassnames(self.classmap, type)
            if type.find(',') != -1:
                args = type.split(',')
                type = args[0].split(' ')[0] + args[-1]
            # print type
            if entry_type == 'member':
                if entry.extensions['access'] != 'public':
                    continue
                clsname = ''
                if 'class' in entry.extensions.keys():
                    clsname = entry.extensions['class']
                #result += "//" + line.strip() + "\n"
                # if not static:
                result += "VERIFY(engine->RegisterObjectProperty(\"%(shortclassname)s\", \"%(type)s %(name)s\", offsetof(%(classname)s, %(name)s)));\n" % \
                    {
                        'type': type,
                        'classname': clsname,
                        'shortclassname': self.getShortClassName(clsname),
                        'name': entry.name
                    }
                #result += "\n"

            elif entry_type in ['function', 'prototype']:
                if 'access' in entry.extensions.keys() and entry.extensions['access'] != 'public':
                    continue
                lname = entry.name
                if len(type) > 0 and type[-1] != '@':
                    lname = ' ' + lname
                elif len(type) > 0 and type[-1] == '@':
                    type = type[:-1]
                    lname = ' @' + lname
                #result += "//" + line.strip() + "\n"
                if not entry.name in self.behaviormap.keys():
                    # normal function

                    # fix classless functions
                    if not 'class' in entry.extensions:
                        entry.extensions['class'] = ''

                    if entry.name == self.getShortClassName(entry.extensions['class']) or entry.name.find('~') != -1:
                        result += "// constructor/destructor: (FIX MANUALLY!) \n//"

                    #type = type.replace('const', '').strip()

                    # replace type with known type
                    for tm in self.typemap.keys():
                        if type[:len(tm)] == tm:
                            type = type.replace(tm, self.typemap[tm])

                    if type.strip() == '':
                        type = 'void '

                    # print '1>>',entry.extensions['signature']
                    as_signature = self._processSignatureASDecl(
                        entry.extensions['signature'])
                    cpp_signature = self._processSignatureASDecl(
                        entry.extensions['signature'], True)
                    result += "VERIFY(engine->RegisterObjectMethod(\"%(shortclassname)s\", \"%(type)s%(name)s%(as_signature)s\", asMETHODPR(%(classname)s,%(name)s, %(cpp_signature)s, %(type)s), %(calling_convention)s));\n" % \
                        {
                            'type': type,
                            'classname': entry.extensions['class'],
                            'shortclassname': self.getShortClassName(entry.extensions['class']),
                            'name': lname,
                            'as_signature': as_signature,
                            'cpp_signature': cpp_signature,
                            'calling_convention': self.calling_convention
                        }
                    #result += "\n"
                else:
                    # behavior
                    behaviortype = self.behaviormap[entry.name]
                    lname = lname.replace(entry.name, 'f')
                    # print lname
                    # print type
                    type = type[0:type.find('operator')].strip()
                    # rearrange the & sign
                    if type[-1] == '&':
                        type = type[:-1]
                        lname = ' &' + lname.strip()
                    as_signature = self._processSignatureASDecl(
                        entry.extensions['signature'])
                    result += "VERIFY(engine->RegisterObjectBehaviour(\"%(shortclassname)s\", %(behaviortype)s, \"%(type)s%(name)s%(signature)s\", asMETHODPR(%(classname)s,%(realname)s, %(signature)s, %(type)s), %(calling_convention)s));\n" % \
                        {
                            'behaviortype': behaviortype,
                            'type': type,
                            'classname': entry.extensions['class'],
                            'shortclassname': self.getShortClassName(entry.extensions['class']),
                            'name': lname,
                            'realname': entry.name,
                            'signature': as_signature,
                            'calling_convention': self.calling_convention
                        }
                    #result += "\n"

                # print entry.name, '\t\t', entry.extensions['signature']
            elif entry_type == 'class':
                lastClass = entry.name
                result += "VERIFY(engine->RegisterObjectType(\"%(classname)s\", sizeof(%(classname)s), asOBJ_REF));\n" % {
                    'classname': entry.name}
        return result

    def generateFromFiles(self, files):
        # load files into memory
        self.files = files
        self.filecontent = {}
        for file in files:
            f = open(file, 'r')
            self.filecontent[file] = f.readlines()
            f.close()

        # create the class
        ctags = exuberant_ctags(tag_program=self.ctags_path, files=files)

        # you can generate a ctags_file instance right away
        # ctags_file is what parses lines from the generator or a
        # tags file and creates a list of ctags_entry instances
        tag_file = ctags.generate_object()

        # override the default run parameters for exuberant ctags, so we get
        # full kind names, say
        tag_file = ctags.generate_object(generator_options={
                                         '--fields': '+afmikKlnsStz', '-F': None, '--c++-kinds': '+cegfmnpstv '})

        harvester = kind_harvester()
        harvester.process_tag_list(tag_file.tags)
        kinds = harvester.get_data()
        # print kinds
        lastClass = ''

        result = ""

        # collect classes
        self.classmap = {}
        for entry_type in kinds.keys():
            if entry_type != 'class':
                continue
            for entry in kinds[entry_type]:
                ns = ''
                if 'namespace' in entry.extensions.keys():
                    ns = entry.extensions['namespace'] + '_'
                #self.classmap[entry.name] = ns + entry.name + 'Class'
                if self.use_namespace_names:
                    self.classmap[entry.name] = ns + entry.name
                else:
                    self.classmap[entry.name] = entry.name

        # this sorts the result a bit depending on the type
        result = ''
        entry_types = ['class', 'member', 'function', 'prototype']
        for entry_type in entry_types:
            if entry_type in kinds.keys():
                res = self._handleKind(kinds, entry_type)
                if res != '':
                    result += "/// %s\n" % str(entry_type)
                    result += res

        self.result = result.strip()
        print "processed %d tags. output files written" % (len(tag_file.tags))
        return len(tag_file.tags)

"""
# example usage:
asig = AngelScriptInterfaceGenerator()
if asig.generateFromFiles(['OgreVector3.h']) > 0:
	asig.saveGenerateHeader()
	asig.saveGenerateCppFile()
"""

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: %s file1.h file2.h ..." % os.path.basename(sys.argv[0])
        sys.exit(1)
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

    # start the generator
    asig = AngelScriptInterfaceGenerator()
    if asig.generateFromFiles(files) > 0:
        asig.saveGenerateHeader()
        asig.saveGenerateCppFile()
