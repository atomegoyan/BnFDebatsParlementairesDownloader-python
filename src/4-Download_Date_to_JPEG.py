# Files
import sys
import os

# Regexp
import re

# Date
import datetime

# HTTP & URL
import urllib.request

### Contains small tools for dates and others
import MyCommonTools

#############################################################################
## The objective of this module is to download all of the JPG of an Ark ID ##
#############################################################################
##
## For example, from this Ark ID :
# ark_id = "/12148/bpt6k6494792j"
## ...build these URL...
# url_short = "https://gallica.bnf.fr/ark:/12148/bpt6k6494792j"
# url_full = "https://gallica.bnf.fr/ark:/12148/bpt6k6494792j/f1.image/f1.jpeg?download=1"
## ...and finally downloading the 4 JPG.
##
## !!! WARNING !!!
##
## The first "f" is useless for progressing in the documents !
## Only the second one is important !!!
## For getting the page 2, you MUST access :                   v
##   https://gallica.bnf.fr/ark:/12148/bpt6k6494792j/f1.image/f2.jpeg
## or :
##   https://gallica.bnf.fr/ark:/12148/bpt6k6494792j/f2.image/f2.jpeg
##
##
## => In order to stop at the end, the module tries to download one more file
##    and when an HTTP error is produced, than, no more pictures are available
##
##############################################################################

# File containing the last line read
g_file_last_line_name = "__last_ark_id_jpeg_downloaded.cache"

# File with unresolved URL
prefix_undownloaded_file_name = "undownloaded_"

### Small tools

# Split the Ark ID into a list
def split_ark_id(ark_id):
    # Ark ID : /12148/bpt6k6449020t
    #match = re.match("/([a-aA-Z_0-9]*)", ark_id)
    #return (match.groups())
    # Spli the string by the '/' and remove the empty 1st
    split = re.split("/", ark_id)
    return (split[1:len(split)])

# Add a URL to the undownloaded log
def update_file_undownloaded_log(msg):
    ark_id_filename_input = os.path.basename(sys.argv[2])
    undownloaded_filename = prefix_undownloaded_file_name + ark_id_filename_input
    MyCommonTools.update_file_ouput(msg, undownloaded_filename)


### Main JPEG downloader

# Download each JPG until an error 503 occurs (when the end of document is reached)
### identifier = ark_id
### directory = directory where to put files
### prefix_filename = output file prefix
def get_document_debat_parlementaire(ark_id, directory_output, filename_prefix):
    print("#### Processing document " + str(ark_id) +
          " to " + str(directory_output) + "/" + str(filename_prefix))
    print("")

    MyCommonTools.prepare_out_directory(directory_output)

    page_exist = True
    page = 1
    while (page_exist):
        # Try to download a page
        print("## Downloading page " + str(page) + " (" + ark_id + ")")

        # Filename of the JPEG after download
        jpgfile = filename_prefix + "_" + str(page) + ".jpeg"

        # URL of the JPEG to reach for this Ark ID
        #url = 'http://gallica.bnf.fr/ark:' + ark_id + '/f' + str(page) + '.image/f' + str(page) +'.jpeg?download=1'
        url_gallica_prefix = 'http://gallica.bnf.fr/ark:'
        url_ark_id = ark_id
        url_page = '/f' + str(page) + '.image/f' + str(page) + '.jpeg?download=1'
        url = url_gallica_prefix + url_ark_id + url_page

        # Prepare request
        req = urllib.request.Request(url)
        print("trying request...")
        try:
            # Send request
            response = urllib.request.urlopen(req)

        # Exception HTTP Error
        except urllib.error.HTTPError as e:
            ## Error 503 : we reached the end of the document
            if (page == 1):
                print("### HTTP ERROR ON PAGE 1:")
            else:
                print("### HTTP ERROR:")

            if hasattr(e, 'reason'):
                print('Failed to reach a server.')
                print('Reason: ', e.reason)
            if hasattr(e, 'code'):
                print('The server couldn\'t fulfill the request.')
                print('Error code: ', e.code)
                ## Error 503 : we reached the end of the document
                if ((int(e.code) == 503) and (page != 1)):
                    print("# Stopped at page " + str(page) + " with HTTP 503")
                    return (None)
            print("# Stopped at page " + str(page))
            print("#############")
            print(e.read())
            print("#############")

            page_exist = False
            return (None)

        # Exception URL Error
        except urllib.error.URLError as e:
            print("### URL ERROR:")
            if hasattr(e, 'reason'):
                print('We failed to reach a server.')
                print('Reason: ', e.reason)
            if hasattr(e, 'errno'):
                print('The server couldn\'t fulfill the request.')
                print('Error code (errno): ', e.errno)
            print("# Stopped at page " + str(page))
            print("#############")
            if hasattr(e, 'read'):
                print(e.read())
            else:
                print("(no e.read())")
            print("#############")

            page_exist = False
            return (None)

        # All other exceptions
        except Exception as e:
            print("### UNKNOWN ERROR:")
            print(str(e))
            print("#############")
            return (None)

        # Everything is fine
        else:
            print("OK - p." + str(page))

            # Get HTTP response
            data = response.read()
            info = response.info()
            url_new = response.url
            headers = response.headers
            status = response.status
            #text = data.decode(info.get_param('charset', 'utf-8'))
            #text = data.decode('utf-8')
            print("## url_new : " + str(url_new))
            print("## headers : " + str(headers))
            print("## status  : " + str(status))

            # Write out the current file
            out_file = open(directory_output + "/" + jpgfile, 'wb')
            out_file.truncate(0)
            out_file.write(data)
            out_file.close()

            print("###################################")
            page += 1

    # Let's return the number of pages written
    return (page)


# For each line, try to download all of the JPEG
def process_lines(lines):
    # File has been read and is in memory, everything is fine
    cur_line = 0
    max_line = len(lines)
    ## Open the temporary file for last processed line
    if (os.path.isfile(g_file_last_line_name)):
        fd = open(g_file_last_line_name, "r")
        file_last_line = fd.read()
        fd.close()
        cur_line = int(file_last_line)

    ## Update the undownloaded log for saying an instance has been launched
    now = datetime.datetime.now()
    update_file_undownloaded_log("# Launching Ark ID downloader for debates at " +
                                 now.strftime("%d/%m/%Y %H:%M:%S"))

    ## Prepare output directory
    dirname_output = sys.argv[1]

    ## Continue the process of the file from the last state
    while (cur_line != max_line):
        #ark_id = lines[cur_line]
        ### Manages file with 2 columns
        line = lines[cur_line]
        line_split = re.split(" ", line)
        date = line_split[0]
        ark_id = line_split[1]
        ###

        ark_id_splitted = split_ark_id(ark_id)
        dirname = dirname_output + "_WIP_JPG" + "/" + date + "_" + str(ark_id_splitted[1])
        filename_prefix = date + "_" + str(ark_id_splitted[1])

        # Ark ID, directory output, filename prefix
        pages_written = get_document_debat_parlementaire(ark_id,
                                                         dirname,
                                                         filename_prefix)

        ## If an error occurred, let's save where we were
        #if (pages_written == None):
        #    update_file_last_line(cur_line, g_file_last_line_name)
        #    update_file_error_log("Failed at line " + str(cur_line))
        #    update_file_error_log("Ark ID : " + ark_id)
        #    return (-3)

        ## If only one page were written... do something ? [probably unusable]
        #if (pages_written == 1):
        #    update_file_unresolved_log(url)
        #    cur_line += 1
        #    continue
        ######################

        print("#############################################################")
        # read next line
        cur_line += 1

    # If everything ended well, let's remove the cache file with last state
    if (os.path.exists(g_file_last_line_name)):
        os.remove(g_file_last_line_name)
    # And let's rename the folder by adding a "_FINAL" inside
    dirname_final = dirname_output + "_JPG" + "_" + MyCommonTools.get_date_and_time()
    os.rename(dirname_output + "_WIP_JPG",  dirname_final)

    return (0)

# Check for arguments in the CLI
def main():
    # Check for missing arguments
    if (len(sys.argv) != 3):
        print("Missing parameters")
        print("")
        print("Usage: " + sys.argv[0] + " output_folder list_of_Ark_IDs")
        print("")
        print("File list_of_Ark_IDs format: [one Ark ID per line]")
        print("[date] [Ark ID]")
        print("date : YYYY-MM-DD     Ark ID : /12148/bpt6k64490143")
        exit(-1)
    else:
        ark_id_filename_input = sys.argv[2]
        # Check if file is readable
        try:
            with open(ark_id_filename_input) as fd:
                ## Put the whole file in memory in a list
                lines = [line.rstrip() for line in fd]
                #### OR ####
                ## Read and process file line by line (one read per line)
                #for line in fd:
                #    print(line.rstrip())

        # If file is unreadable, let's manage the exception
        except IOError:
            print("File " + ark_id_file_input + " must exist and be readable")
            print("")
            print("Usage: " + sys.argv[0] + " output_folder list_of_Ark_IDs")
            print("")
            print("File list_of_Ark_IDs format: [one Ark ID per line]")
            print("[date] [Ark ID]")
            print("date : YYYY-MM-DD     Ark ID : /12148/bpt6k64490143")
            exit(-2)


        # In other case, when evrything is fine, let's process lines
        ret = process_lines(lines)

        exit(ret)

main()
