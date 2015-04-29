#coding=utf-8

def ip_str2int(str_ip):
	tmp = str_ip.split('.')
	return (int(tmp[0]) << 24) + (int(tmp[1]) << 16) + (int(tmp[2]) << 8) + int(tmp[3])

def ip_int2str(int_ip):
	return "%u.%u.%u.%u" % (((int_ip & 0xFF000000) % 0x00FFFFFF), ((int_ip & 0x00FF0000) % 0x0000FFFF), ((int_ip & 0x0000FF00) % 0x000000FF), (int_ip & 0x000000FF))
