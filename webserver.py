import sys, string, cgi, time, traceback, threading, SocketServer, BaseHTTPServer, zipfile, random
from generator import *

# set by subverison upon commit
SVN_REVISION = "$Rev$"
SVN_ID       = "$Id$"

class GenericOptions:
	pass

def uniqueTask():
	# faked one to prevent existing directories
	uid = str(random.random()).replace('.', '')

	# create base path
	for path in ['input', 'output']:
		if not os.path.isdir(path):
			os.mkdir(path)
	# create unique path
	ipath = os.path.join("input", uid)
	opath = os.path.join("output", uid)
	os.mkdir(ipath)
	os.mkdir(opath)
	return (uid, ipath, opath)

class worker(threading.Thread):
	def __init__(self, evdone, evdestroy, ipath, opath, wfile, options):
		self.opath = opath
		self.ipath = ipath
		self.wfile = wfile
		self.evdone=evdone
		self.evdestroy=evdestroy
		
		self.options = options
		threading.Thread.__init__(self)
		
	def run(self):
		asig = AngelScriptInterfaceGenerator()
		nfiles = []
		files = os.listdir(self.ipath)
		for f in files:
			nfiles.append(os.path.join(self.ipath, f))
		files = nfiles
		print files
		if asig.generateFromFiles(files) > 0:
			self.header = asig.generateHeader()
			self.source = asig.generateCppFile()

		#print "worker done"
		self.evdone.set()
		#print "worker waiting"
		self.evdestroy.wait()
		#print "worker destroyed"


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
	def do_GET(self):
		#print self.path
		#print self.path
		if self.path == "/":
			content= """
<HTML><BODY>

<h1>AngelScript Interface Generator</h1>
This is a generator which takes header files and generates you a fitting registration list for angelscript.<p/>	

You can upload the following filetypes that contain the sources:<br/>
.zip .h .hh .hpp .hxx .cpp .cxx .cc .c .txt (Use .zip to upload multiple files at once)
<form method='POST' enctype='multipart/form-data' action=''>

<table border="0">

<tr><td>Namespace Mode</td><td>
	<select name="namespacemode">
	 <option value="0">Add Namespaces to class names</option>
	 <option value="1" selected>Just the pure class names, no namespaces</option>
	</select></td>
</tr>

<tr><td>&nbsp;</td><td><label><input type="checkbox" name="operators" checked>generate operators</label></td></tr>

<tr><td>File</td><td><input type='file' name='upfile'></td></tr>
<tr><td colspan="2">

<input type='submit' value='Generate'>
</td></tr>
</table>

</form>
<div style="font-size:x-small;color:#aaaaaa;position:absolute;right:0px;bottom:0px;">(ASIG revision %(rev)s)</div>
</BODY>
</HTML>
			""" % {'rev':SVN_REVISION}
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			self.wfile.write(content)
		"""
		# not used for this
		if self.path.startswith('/output/'):
			base, filename = os.path.split(self.path)
			
			fpath = self.path
			if sys.platform.startswith('linux'):
				fpath = fpath.lstrip('/')
			else:
				fpath = fpath.replace('/', '\\')
				fpath = fpath.lstrip('\\')
			
			if not os.path.isfile(fpath):
				self.send_response(404)
				self.end_headers()
				self.wfile.write("404 - file not found!")
				return
			file = open(fpath, 'rb')
			content = file.read()
			file.close()
			
			self.send_response(200)
			self.send_header('Content-Length', len(content))
			self.send_header('Content-type', 'application/octet-stream')
			self.send_header('Content-Disposition', filename)
			self.end_headers()
			self.wfile.write(content)
		"""

	def do_POST(self):
		try:
			# Parse the form data posted
			form = cgi.FieldStorage(
				fp=self.rfile,
				headers=self.headers,
				environ={'REQUEST_METHOD':'POST',
						 'CONTENT_TYPE':self.headers['Content-Type'],
						 })	
			
			#print form
			
			# Echo back information about what was posted in the form
			#for field in form.keys():
			#	print field, form[field]
			
			#ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			#if ctype == 'multipart/form-data':
			#	query=cgi.parse_multipart(self.rfile, pdict)
			
			self.send_response(200)
			self.send_header('Content-type', 'text/html')
			self.end_headers()
			
			upfilecontent = form['upfile'].file.read()
					
			
			options = GenericOptions()
			options.generate_operators = ('generate_operators' in form.keys())

			options.namespacemode = 1
			if 'namespacemode' in form.keys():
				options.namespacemode = int(form['namespacemode'].value)
			
			# create unique directories
			uid, ipath, opath = uniqueTask()
			
			ufilename = "upload.zip"
			#print form
			if 'upfile' in form.keys():
				ufilename = form['upfile'].filename
			
			if ufilename == '':
				self.wfile.write("error: no file selected!<p>")
				return
			#print ufilename

			self.wfile.write("<html><body>got the file, processing (this can take several seconds)...<p>")
			self.wfile.flush()
			
			root, ext = os.path.splitext(ufilename)
			if ext.lower() in '.h .hh .hpp .hxx .cpp .cxx .cc .c .txt'.split():
				# save uploaded file
				dstfile = os.path.join(ipath, ufilename)
				#print dstfile
				fo = open(dstfile, "wb")
				fo.write(upfilecontent)
				fo.close()
				
			elif ext.lower() == '.zip':
				# save uploaded file
				dstfile = os.path.join(ipath, ufilename)
				#print dstfile
				fo = open(dstfile, "wb")
				fo.write(upfilecontent)
				fo.close()
				
				#try to unpack uploaded file
				#print dstfile
				if not zipfile.is_zipfile(dstfile):
					self.wfile.write("error: uploaded file is no valid zip file!<p>")
					return
				zfile = zipfile.ZipFile(dstfile, "r")
				#zfile.printdir()
				self.wfile.write("- unzipping ...<br/>")
				self.wfile.flush()
				for info in zfile.infolist():
					fname = info.filename
					# decompress each file's data
					data = zfile.read(fname)
					filename = os.path.join(ipath, fname)
					#print filename
					fout = open(filename, "wb")
					fout.write(data)
					fout.close()
					
					self.wfile.write("- unzipped %s<br/>" % (fname))
					self.wfile.flush()
				
				del zfile
				# remove the .zip file again
				os.unlink(dstfile)
			else:
				self.wfile.write("only .zip Archives or source/header files allowed. Please go back and try again.")
				self.wfile.flush()
				return
			
			# setup threads and evnet stuff
			evdone = threading.Event()
			evdestroy = threading.Event()
			

			w = worker(evdone, evdestroy, ipath, opath, self.wfile, options)
			w.start()
			
			self.wfile.write("<br/>worker started, this can take some time<br/>")
			self.wfile.flush()
			
			#evdone.wait()
			# pseudo-update the client, so he knows we are still alive
			while not evdone.isSet():
				evdone.wait(1)
				self.wfile.write(".")
				self.wfile.flush()
			
			self.wfile.write("DONE!<p/>")
			
			outtemplate = """<h2>output.h</h2>
<textarea style='width:100%%;height:300px;'>%(header)s</textarea><p/>

<h2>output.cpp</h2>
<textarea style='width:100%%;height:300px;'>%(source)s</textarea><p/>
"""
			content = outtemplate % {'header':w.header, 'source':w.source}
			
			self.wfile.write(content)
			self.wfile.write("<br/>you can restart <a href='/'>here</a>")
			self.wfile.flush()
			
			evdestroy.set()
			w.join()
			
			for f in os.listdir(ipath):
				os.unlink(os.path.join(ipath, f))
			os.rmdir(ipath)
			os.rmdir(opath)
			
		except Exception, e:
			print("error:")
			print(str(e))
			print(traceback.format_exc())

class myHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass
	
def main():
	try:
		server = myHTTPServer(('', 8080), MyHandler)
		print 'started httpserver...'
		server.serve_forever()
	except KeyboardInterrupt:
		print '^C received, shutting down server'
		server.socket.close()

if __name__ == '__main__':
	main()