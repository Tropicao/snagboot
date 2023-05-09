# This file is part of Snagboot
# Copyright (C) 2023 Bootlin
# 
# Written by Romain Gantois <romain.gantois@bootlin.com> in 2023.
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import os
from snagflash.utils import int_arg
import shutil
import tempfile
from snagflash.bmaptools import BmapCreate
from snagflash.bmaptools import BmapCopy
import sys
import logging
logger = logging.getLogger("snagflash")

BIG_FILE_THRESHOLD = 0x1000000

def bmap_copy(filepath: str, dev, src_size: int):
	mappath = os.path.splitext(filepath)[0] + ".bmap"
	mapfile = None
	print(f"Looking for {mappath}...")
	gen_bmap = True
	if os.path.exists(mappath):
		gen_bmap = False
		mapfileb = open(mappath, "rb")
		#check if the bmap file is clearsigned
		#if it is, we shouldn't handle it, since
		#I'd prefer to avoid depending on the gpg package
		hdr = mapfileb.read(34)
		if hdr == b"-----BEGIN PGP SIGNED MESSAGE-----":
			logger.warning("Bmap file found is clearsigned, skipping...")
			gen_bmap = True
		else:
			mapfileb.seek(0)
	if gen_bmap:
		print("Generating bmap...")
		try:
			mapfile = tempfile.NamedTemporaryFile("w+")
		except IOError as err:
			raise Exception("Could not create temporary file for bmap")
		mapfile.flush()
		mapfile.seek(0)
		creator = BmapCreate.BmapCreate(filepath, mapfile, "sha256")
		creator.generate(True)
		mapfileb = open(mapfile.name, "rb")

	with open(filepath, "rb") as src_file:
		writer = BmapCopy.BmapBdevCopy(src_file, dev, mapfileb, src_size)
		writer.copy(False, True)
	mapfileb.close()
	if not mapfile is None:
		mapfile.close()

def write_raw(args):
	devpath = args.blockdev
	filepath = args.src
	if not os.path.exists(devpath):
		raise ValueError(f"Device {devpath} does not exist")
	if not os.path.exists(filepath):
		raise ValueError(f"File {filepath} does not exist")
	with open(filepath, "rb") as file:
		blob = file.read(-1)
	if not args.size is None:
		size = int_arg(args.size)
	else:
		size = len(blob)
	with open(devpath, "rb+") as dev:
		bmap_copy(filepath, dev, size)

def ums(args):
	if args.dest:
		shutil.copy(args.src, args.dest)
	if args.blockdev:
		write_raw(args)

