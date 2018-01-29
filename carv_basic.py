import os, errno #For folder creation 

target = "8-jpeg-search.dd"
bytesRead = 0
imageFound = None
image = []
imageName = ""

def saveImage(image, imageName, passN):
	imagePath = "carved/"+ passN +"/" + imageName + ".jpg"
	isJPG = True
	
	#Create folders if they do not exist
	#https://stackoverflow.com/questions/273192/how-can-i-create-a-directory-if-it-does-not-exist?rq=1
	try:
		os.makedirs("carved/" + passN)
	except OSError as e:
		if e.errno != errno.EEXIST:
			raise
	
	#Check for JFIF in order to remove scrap images
	# for i, byte in enumerate(image):
		# if byte == b'\x4a': # Look for J
			# if image[i + 1] == b'\x46' and image[i + 2] == b'\x49' and image[i + 3] == b'\x46': #Look for FIF after J
				# isJPG = True
				# break
	
	if(isJPG):
		with open(imagePath, "wb") as file:
			for byte in image:
				file.write(byte)
			file.close()
		print("Image saved: %s" % (imagePath))

#Header|Footer carving
print("Header|footer carving\n--- Pass 1 (JPG) ---\n")
with open(target, "rb") as file:
	byte = file.read(1)
	bytesRead += 1
	while byte:
		#Check for header | FFD8 + FFD8/FFE0/FFE1
		#https://en.wikipedia.org/wiki/List_of_file_signatures
		if byte == b'\xff' and not imageFound:
			byte = file.read(1)
			bytesRead += 1
			if byte == b'\xd8':
				byte = file.read(2)
				bytesRead += 2
				if byte == b'\xff\xd8' or byte == b'\xff\xe0' or byte == b'\xff\xe1':
					imageFound = True
					image.append(b'\xff\xd8')
					image.append(byte)
					imageName = str(bytesRead) + "-"
				else: print("Bamboozle header found at %s" % (bytesRead))
			else: continue # To avoid situations such as FF FF D8
			
		byte = file.read(1)
		bytesRead += 1
		
		#Check for footer and append image bytes
		if imageFound:
			image.append(byte)
			if byte == b'\xff':
				byte = file.read(1)
				bytesRead += 1
				image.append(byte)
				if byte == b'\xd9':
					imageFound = None
					imageName += str(bytesRead)
					saveImage(image, imageName, "pass1")
					image = []
	bytesRead = 0
	file.close()
	
bytesRead = 0
headerOffsets = []
#https://en.wikipedia.org/wiki/JPEG#Effects_of_JPEG_compression
qBitSize = 8.25 #The pixel size in bits (Quality)
height = 1080	#Image height (px)
width = 1920	#Image width (px)
bytesToRead = int(((height*width) * qBitSize)/8)
print("\nHeader|max length carving (max size of 1920x1080 & quality=100)\n--- Pass 2 (JPG) ---\n")
with open(target, "rb") as file:
	byte = file.read(1)
	bytesRead += 1
	while byte:
		#Check for header FFD8
		if byte == b'\xff':
			byte = file.read(1)
			bytesRead += 1
			if byte == b'\xd8':
				headerOffsets.append(bytesRead - 2)
		byte = file.read(1)
		bytesRead += 1
	
	for offset in headerOffsets:
		image = []
		file.seek(offset, 0)
		for i in range(0, bytesToRead):
			image.append(file.read(1))
		saveImage(image, str(offset), "pass2")
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	