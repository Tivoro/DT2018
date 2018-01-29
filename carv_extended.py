import os, errno #For folder creation 

target = "8-jpeg-search.dd"
#target = "11-carve-fat.dd"
#target = "12-carve-ext2.dd"
offsetsJPG = []
offsetsPDF = []
offsetsGIF = []

#Save the carved
def saveImage(image, imageName, type, src, extension):
	target = src.replace(".", "")
	imagePath = target + "/" + type + "/" + imageName + extension
	
	#Create folders if they do not exist
	#https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist?rq=1
	try:
		os.makedirs(target + "/" + type)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
	
	with open(imagePath, "wb") as file:
		for byte in image:
			file.write(byte)
		file.close()
	print("%s saved: %s" % (type, imagePath))
#Find header offsets for JPG, PDF and GIF
def findOffsets(target):
	with open(target, "rb") as file:
		byte = file.read(1)
		while byte:
			#Check for JPG
			if byte == b'\xff':
				byte = file.read(1)
				if byte == b'\xd8':
					byte = file.read(2)
					if byte == b'\xff\xd8' or byte == b'\xff\xe0' or byte == b'\xff\xe1':
						offsetsJPG.append(file.tell() - 4) #Save the offset
						print("Found potential JPG @%s" % (file.tell() - 4))
					else:
						file.seek(file.tell() - 2)
				else:
					file.seek(file.tell() - 1) # To avoid situations such as FF FF D8 ...
			
			#Check for PDF
			if byte == b'\x25':
				byte = file.read(3)
				if byte == b'\x50\x44\x46':
					offsetsPDF.append(file.tell() - 4)
					print("Found potential PDF @%s" % (file.tell() - 4))
				else:
					file.seek(file.tell() - 3)
					
			#Check for GIF
			if byte == b'\x47':
				byte = file.read(5)
				if byte == b'\x49\x46\x38\x37\x61' or byte == b'\x49\x46\x38\x39\x61':
					offsetsGIF.append(file.tell() - 6)
					print("Found potential GIF @%s" % (file.tell () - 6))
				else:
					file.seek(file.tell() - 5)

			byte = file.read(1)
		file.close()

findOffsets(target)

with open(target, "rb") as file:
	EOF = None
	image = []
	#I decided to go with the 1920x1080 & 100q again
	bytesToRead = int((1920*1080*8.25)/8)
	
	print("\nJPG carving using max file size\n")
	for offset in offsetsJPG:
		file.seek(offset)
		for i in range(0, bytesToRead):
			image.append(file.read(1))
		saveImage(image, str(offset) +"-"+ str(file.tell()), "JPG", target, ".jpg")
		image = []
	
	print("\nPDF carving using header/footer\n")
	for offset in offsetsPDF:
		file.seek(offset)
		byte = file.read(1)
		while not EOF:
			image.append(byte)
			if byte == b'\x25':
				byte = file.read(4)
				if byte == b'\x25\x45\x4f\x46':
					image.append(byte)
					saveImage(image, str(offset)+"-"+str(file.tell()), "PDF", target, ".pdf")
					EOF = True
				else:
					file.seek(file.tell() - 4)
			byte = file.read(1)
		image = []
		EOF = None
	
	#I found http://www.file-recovery.com/gif-signature-format.htm which explains how GIFs are structured
	print("\nGIF carving using file structure\n")
	for offset in offsetsGIF:
		file.seek(offset)
		
		#Get some header data
		image.append(file.read(6)) #File signature
		width = file.read(2); image.append(width)
		height = file.read(2); image.append(height)
		flags = file.read(1); image.append(flags)	#Used to calculate the color table (I think)
		
		if '{:08b}'.format(ord(flags))[0] == "1": #Check if the highest bit is set
			GCTSize = (1 << ((ord(flags) & ord(b'\x07')) + 1)) * 3
			image.append(file.read(GCTSize + 2)) #I didn't read 2 bits from the header
			
		while not EOF:
			byte = file.read(1)
			image.append(byte)
			
			#Check what type of block we're on
			if byte == b'\x21': #Extension block
				byte = file.read(1); image.append(byte)
				if byte == b'\xff': #Application extension block (NETSCAPE)
					dataLen = file.read(1); image.append(dataLen)
					image.append(file.read(ord(dataLen)))
					moreData = file.read(1); image.append(moreData)
					image.append(file.read(ord(moreData)))
					EOB = file.read(1); image.append(EOB)
					if EOB == b'\x00': 
						continue
					else: 
						print ("Hmmm..."); break
				if byte == b'\xfe': #Application extension block (Built with the GIF movie gear)
					dataLen = file.read(1); image.append(dataLen)
					image.append(file.read(ord(dataLen)))
					EOB = file.read(1); image.append(EOB)
					if EOB == b'\x00':
						continue
					else: 
						print("Hmmm..."); break
				if byte == b'\xf9': #8-byte extension block
					image.append(file.read(6))
					continue
			
			if byte == b'\x2c': #Image block
				#Block header
				tlPixel = file.read(4); image.append(tlPixel) #Top left pixel
				brPixel = file.read(4); image.append(brPixel) #Bottom right pixel
				image.append(file.read(1)) #Unknown byte
				flags = file.read(1); image.append(flags)
				
				if '{:08b}'.format(ord(flags))[0] == "1": #Check if the highest bit is set
					GCTSize = (1 << ((ord(flags) & ord(b'\x07')) + 1)) * 3
					image.append(file.read(GCTSize + 2)) #I didn't read 2 bits from the header
				
				#Get all the sub block (0 terminated)
				len = file.read(1); image.append(len)
				while len != b'\x00':
					image.append(file.read(ord(len)))
					len = file.read(1); image.append(len)
				continue
				
			if byte == b'\x3b': #EOF
				saveImage(image, str(offset)+"-"+str(file.tell()), "GIF", target, ".gif")
				break
			#If something goes wrong I might aswell save a partial GIF for inspection
			saveImage(image, str(offset)+"-"+str(file.tell())+"-partial", "GIF", target, ".gif")
			break;