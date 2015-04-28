#!/usr/bin/python

import optparse
import socket
import sys
import  os
from collections import defaultdict
try:
    import GeoIP
except ImportError:
    print "Error: Maxmind GeoIP Python Module is required and not installed. Please install from: https://github.com/maxmind/geoip-api-python"
    sys.exit()
try:
    from prettytable import PrettyTable
except ImportError:
    print "Error: PrettyTable is required and not installed. Please install it by running 'pip install prettytable'"
    sys.exit()

# MaxMind GeoIP databases should be updated monthly (GeoIP.dat, GeoIPASNum.dat, GeoLiteCity.dat)
# http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz
# http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz
# http://geolite.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz

def geoip_query(ip_address):
    try:
        # GeoLiteCity Database
        try:
            gi = GeoIP.open("GeoLiteCity.dat", GeoIP.GEOIP_STANDARD)
        except:
            print "Please download and gunzip the latest version from http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz"
            sys.exit()
        record = gi.record_by_addr(ip_address)
        if record['city'] is None: city = "Unknown"
        else: city = record['city']
        if record['region_name'] is None: region_name = "Unknown"
        else: region_name = record['region_name']
        longitude = record['longitude']
        latitude = record['latitude']
        country_code = record['country_code']
        country_name = record['country_name']

        # GeoIPASNum Database
        try:
            go = GeoIP.open("GeoIPASNum.dat", GeoIP.GEOIP_STANDARD)
        except:
            print "Please download and gunzip the latest version from http://geolite.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz"
            sys.exit()
        as_number, as_name = str(go.org_by_addr(ip_address)).split(" ", 1)
        as_number = as_number.strip("AS")

        # Google Maps URL
        gmap_url = "http://maps.google.com/maps?f=q&source=s_q&hl=ca&geocode=&q=" \
                   + str(latitude) + "+" + str(longitude)

        # Fix encoding issues
        as_name = as_name.decode('utf-8', 'ignore')
        city = city.decode('utf-8', 'ignore')
        region_name = region_name.decode('utf-8', 'ignore')
        country_name = country_name.decode('utf-8', 'ignore')
        
        return [ip_address, as_number, as_name, city, region_name, country_name,
                country_code, str(latitude), str(longitude), gmap_url]

    except ValueError:
        as_number = str(go.org_by_addr(ip_address)).strip("AS")
        as_name = "Unknown"
        
    except Exception, e:
        print "Unable to find GeoIP data for '" + str(ip_address) + "'"
        print "Are you sure it's a correctly formatted IP Address?"
        
def single_ip_print(single_ip_info):
    try:
        print "IP Address: " + single_ip_info[0]
        print "AS Number: " + single_ip_info[1]
        print "AS Name: " + single_ip_info[2]
        print "City: " + single_ip_info[3]
        print "Region: " + single_ip_info[4]
        print "Country: " + single_ip_info[5]
        print "Country Code: " + single_ip_info[6]
        print "Latitude: " + single_ip_info[7]
        print "Longitude: " + single_ip_info[8]
        print "Google Maps: " + single_ip_info[9]
        exit(1)
    except Exception, e:
        print "Error displaying the GeoIP information for: " + \
              single_ip_info[0]

def print_csv(ip_data_dict):
    header = ["IP Address", "AS Number", "AS Name", "City", "Region", "Country",
              "Country Code", "Latitude", "Longitude", "Google Maps URL"]
    print str(",".join(header))
    try:
        for ip, info in ip_data_dict.iteritems():
            if info:
                print ",".join(info)
        exit(1)
    except Exception, e:
        print "There was a problem displaying the GeoIP data as a CSV"
        print str(e)

def print_table(ip_data_dict):
    try:
        geoipTable = PrettyTable(
            ["IP Address", "AS Number", "AS Name", "City", "Region", "Country",
             "Country Code", "Latitude", "Longitude", "Google Maps URL"]
            )
        geoipTable.padding_width = 1
        for ip, info in ip_data_dict.iteritems():
            if info:
                geoipTable.add_row(info)
        print geoipTable
        exit(1)

    except UnicodeDecodeError, ue:
        for arg in ue.args:
            arg.decode('iso-8859-1').encode('utf8')
    
    except Exception, e:
        print "There was a problem displaying the GeoIP data in a table format"
        print str(e)


def is_valid_ip(ip_address):
    try:
        socket.inet_aton(ip_address)
        return True
    except:
        return False
    
def main():
    try:
        usage = "usage: %prog <IP Address>\n" + \
                "       %prog -f <filename> (-t or -c)"
        parser = optparse.OptionParser(usage)
        parser.add_option("-f", dest="ip_file",
                          help="Specify a file containing a list of IPs",
                          metavar="<filename>")
        parser.add_option("-t", "--table", dest="table", default=False,
                          action='store_true', 
                          help="Print the results in a formatted table")
        parser.add_option("-c", "--csv", dest="csv", default=False,
                          action='store_true',
                          help="Print the results in a comma separated file")
        (opts, args) = parser.parse_args()

        if len(args) < 1 and opts.ip_file is None:
            parser.print_help()
            exit(-1)

        # If the user specifies a filename, query and store all info in a dict
        if opts.ip_file:
            # User needs to specify an output format
            if opts.table is False and opts.csv is False:
                parser.print_help()
                print "\nPlease choose either table or csv for the output format\n"
                exit(-1)
            else:
                with open(opts.ip_file) as ip_file:
                    ip_list = ip_file.read().splitlines()

                ip_data_dict = defaultdict(list)
                for ip_address in ip_list:
                    if is_valid_ip(ip_address):
                        ip_info = geoip_query(ip_address)
                        ip_data_dict[ip_address] = ip_info
                    else:
                        print "Skipping " + ip_address + ". It's not " + \
                              "a valid IP Address."

                if opts.table is True:
                    print_table(ip_data_dict)
                else:
                    print print_csv(ip_data_dict)
                    
        # If the user didn't specify a filename, just print the details         
        else:
            ip_address = args[0]
            if is_valid_ip(ip_address):
                single_ip_info = geoip_query(ip_address)
                single_ip_print(single_ip_info)
            else:
                parser.print_help()
                print "\n Error: Please provide a valid IP Address\n"
    except Exception, e:
        print "Error: " + str(e)
            
if __name__ == "__main__":
    sys.exit(main())
