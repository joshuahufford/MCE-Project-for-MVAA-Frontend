# JST Transcript Reader

import re
import os

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO


class JSTReader:

    def __init__(self, directory):
        self.dir = directory  # base directory, where JST is uploaded/stored
        # self.wdir = self.dir + 'working/'  # working directory
        self.idir = self.dir + 'images/'  # image directory
        self.tdir = self.idir + 'text/'  # text file directory
        pass

    def clear_dir(self, mkdir):
        # Empty the working directory
        # Currently done by deleting then (if desired) making it again
        os.system('rm -rf ' + self.dir)
        if mkdir:
            os.system('mkdir ' + self.dir)

    def convert_to_image(self, file):
        # Convert the jst file (presumably PDF) into an image (jpg) using imagemagick
        # Command for imagemagick version 6 is "convert-im6 inputfile -density (value) outputfile"
        # Higher density for higher quality, up to a certain point. Will take longer to run at higher values of course
        os.system('mkdir ' + self.idir)
        os.system('(cd ' + self.idir + '; convert-im6 -density 300 ../"' + file + '" image' + '.jpg' + ')')

    def scan_image(self):
        accepted_courses = set()
        rejected_courses = set()
        file_list = []

        os.system('mkdir ' + self.tdir)

        num = int(os.popen('ls ' + self.idir + ' -1 | wc -l').read())

        for i in range(0, num - 1):
            read_command = '(cd ' + self.tdir + '; tesseract ../image' + '-' + str(i) + '.jpg image' + '-' + str(
                i) + ')'
            os.system(read_command)
            filename = self.tdir + 'image-' + str(i) + '.txt'
            file_list.append(filename)

        flag = True
        b = None
        last_b = b
        for i in range(0, num - 1):
            filename = self.tdir + 'image-' + str(i) + '.txt'
            
            # print('----------filename------------')
            # print(filename)
            # print('------------flag---------------')
            # print(flag)
            if flag:
                for line in open(filename):
                    # print(courses)
                    print('--------------LINE---------------')
                    print(line)
                    print(b, "            ", last_b)
                    if "Military Experience" in line or "Other Learning Experiences" in line:
                        flag = False
                        break
                    if line == "":
                        continue
                    if line != "Military Experience":
                        if re.search(r'((MC|NV)-[0-9]+-[0-9]+)', line):
                            print('--------------------- COURSE CODE MATCH IN LINE ---------------------')
                            # print('------------ line ---------------')
                            # print(line)
                            b = re.findall(r'((MC|NV)-[0-9]+-[0-9]+)', line)
                            print('----------------   b    -------------------------------')
                            print(b)
                            # if len(b) > 1:
                            #     last_b = b[1]
                            # else:
                            last_b = b[0][0]
                    if "Credit Is Not Recommended" in line and last_b is not None:
                        # print("No credit: ", last_b)
                        if last_b in accepted_courses:
                            accepted_courses.remove(last_b)
                        print('---------- adding to rejected: ---------------------')
                        print(last_b)
                        rejected_courses.add(last_b)
                    if b is not None:
                        # print("b: ", b)
                        # print("last_b: ", last_b)
                        accepted_courses.add(last_b)
                        # print('------------------- last_b -----------')
                        # print(last_b)
                        b = None
        return accepted_courses, rejected_courses

    def convert_pdf_to_txt(self, path):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos = set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        return text

    def scan_pdf(self):
        # get the list of files from the current directory
        files = os.listdir(self.dir)

        # filter the list of files for only pdf files
        files = [fi for fi in files if fi.endswith(".pdf")]

        # for each pdf
        for pdf in files:
            a = self.convert_pdf_to_txt(self.dir + pdf).strip().split("\n")
            print('------------a value--------------')
            print(a)
            if len(a[0]) > 0:
                print('----------------------------text-based PDF, running as normal--------------------')
                # for line in a:
                # 	print(line +"\n")

                accepted_courses = set()
                rejected_courses = set()
                b = None
                last_b = b
                flag = True
                if flag:
                    for line in a:
                        # print(courses)
                        # the inside of this loop is used twice - could put in a function somewhere somehow
                        if line == "Military Experience" or line == "Other Learning Experiences":
                            flag = False
                            break
                        if line == "":
                            continue
                        if line != "Military Experience":
                            if re.match(r'([A-Z]+-[0-9]+-[0-9]+)', line):
                                b = re.findall(r'([A-Z]+-[0-9]+-[0-9]+)', line)
                                last_b = b[0]
                        if line == "Credit Is Not Recommended":
                            # print("No credit: ", last_b)
                            if last_b in accepted_courses:
                                accepted_courses.remove(last_b)
                            rejected_courses.add(last_b)
                        if b is not None:
                            # print("b: ", b)
                            # print("last_b: ", last_b)
                            accepted_courses.add(last_b)
                            b = None

                course_dict = {}
                course_dict['accepted'] = sorted(list(accepted_courses))
                course_dict['rejected'] = sorted(list(rejected_courses))
            else:  # OCR route
                print('------------------image-based PDF, running conversion------------------------')
                self.convert_to_image(pdf)
                accepted_courses, rejected_courses = self.scan_image()
                print('---------accepted courses----------')
                print(accepted_courses)
                print('------------rejected courses -----------')
                print(rejected_courses)
                course_dict = {}
                course_dict['accepted'] = sorted(list(accepted_courses))
                course_dict['rejected'] = sorted(list(rejected_courses))

        print('--------------------------course dict---------------------')
        print(course_dict)
        return course_dict

