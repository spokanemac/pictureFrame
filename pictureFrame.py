#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  PictureFrame.py
#  
#  Copyright 2021  Jack-Daniyel Strong, J-D Strong Consulting, Inc.
#  
#  Using rclone, this will copy an album to the local disk
#  resize photos to the display size, and then kick off a slide show.
#  Image Resizing logic from https://drjohnstechtalk.com/blog/2021/01/raspberry-pi-photo-frame-using-the-pictures-on-your-google-drive-ii/
#  qiv inpiration and structure from https://github.com/joshholding/pi-photo-frame

import PIL, os, sys, argparse
from pathlib import Path,PurePath
from PIL import Image
from datetime import datetime, timedelta

# SETTINGS
# Where are we storing the images from rclone?
imageFolder = Path("/home/pi/Pictures")
# Where are the resized images going?
imageFolderTemp = Path("/home/pi/PictureFrame")
# rclone remoteName:pathTo/Photos
GPhotosAlbum = "remote:album/Westfall Photo Frame"
# slideshow delay
SlideshowDelay = 30
    
# You shouldn't need to edit below this line
displaywidth = int(os.popen("fbset|grep geometry|awk '{print $2}'").read())
displayheight = int(os.popen("fbset|grep geometry|awk '{print $3}'").read())
# General manipulation Settings
smallscreen = 801
narrowmax = .76
blowupfactor = 1.1
# take less from the top than the bottom
topshare = .3
bottomshare = 1.0 - topshare
starttime = datetime.now()


def init_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        usage="%(prog)s [OPTION]",
        description="rclone photos, resize, and (re)start slideshow"
    )
    ap.add_argument(
        "--version", action="version",
        version = f"{ap.prog} version 1.0.0"
    )
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="increase output verbosity"
    )
    ap.add_argument(
        "-s", "--start", action="store_true", help="start slideshow without rclone"
    )
    return ap
        
    
def main(args):
    parser = init_argparse()
    args = parser.parse_args()
    
    print("Starting PhotoFrame Update", str(starttime))
    if args.verbose:
        print("Display Dimensions: " + str(displaywidth) + " X " + str(displayheight))

    if not args.start:
        # Let's make sure directories exist
        imageFolder.mkdir(exist_ok=True)
        imageFolderTemp.mkdir(exist_ok=True)
        
        # Let's download some images.
        print("Copying Google Photos Album: \"" + GPhotosAlbum + "\" to \"" + str(imageFolder) + "\"")
        rc = os.popen("rclone copy \"" + GPhotosAlbum + "\" \"" + str(imageFolder) + "\"").read()
            
        #Let's process some images.
        # for each image in the directory
        for f in imageFolder.iterdir():
            imageFile = imageFolder / f
            if imageFile.is_file():
                imgResize(imageFile,args)
                
        # Finished Processing Photos
        print("Processing Photos Complete")
    # Stop current display
    print("Stopping Photo Frame.")
    os.system("pkill qiv")
    # Start new Display
    print("Starting Photo Frame.")
    os.system("qiv --watch --maxpect --no_statusbar --slide --random --disable_grab --readonly --fullscreen --autorotate --delay " + str(SlideshowDelay) + " --display :0 "+ str(imageFolderTemp) + " &")
    print("Start Time: ", str(starttime))
    print("End Time: ", str(datetime.now()))
    print("Run Time: ", str(datetime.now()-starttime))
    return 0

def imgResize(imageFile, args):
    resizedFile = imageFolderTemp / imageFile.name
    if resizedFile.exists():
        if args.verbose:
            print("Skipping ", resizedFile)
    else:
        im = Image.open(imageFile)
        width = im.size[0]
        height = im.size[1]
        if args.verbose:
            print("Image File: ", imageFile)
            print("File Extension: ",imageFile.suffix)
            print("image width and height: ",width,height)
     
    # If the aspect ratio is wider than the display screen's aspect ratio,
    # constrain the width to the display's full width
        if width/float(height) > float(displaywidth)/float(displayheight):
            if args.verbose:
                print("In section width contrained to full width code section")
            widthn = displaywidth
            heightn = int(height*float(displaywidth)/width)
            im5 = im.resize((widthn, heightn), Image.ANTIALIAS) # best down-sizing filter
        else:
            heightn = displayheight
            widthn  = int(width*float(displayheight)/height)
            
            if width/float(height) < narrowmax and displaywidth < smallscreen:
                # if width is narrow we're losing too much by using the whole picture.
                # Blow it up by blowupfactor% if display is small, and crop most of it from the bottom
                heightn = int(displayheight*blowupfactor)
                widthn  = int(width*float(heightn)/height)
                im4 = im.resize((widthn, heightn), Image.ANTIALIAS) # best down-sizing filter
                top = int(displayheight*(blowupfactor - 1)*topshare)
                bottom = int(heightn - displayheight*(blowupfactor - 1)*bottomshare)
                if args.verbose:
                    print("heightn,top,widthn,bottom: ",heightn,top,widthn,bottom)
            
                im5 = im4.crop((0,top,widthn,bottom))
            else:
                im5 = im.resize((widthn, heightn), Image.ANTIALIAS) # best down-sizing filter
        im5.save(resizedFile,"JPEG")
        
        print("Image Resized: ",resizedFile)
        im.close()
        im5.close()
        

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
