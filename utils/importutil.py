def my_import(name):
	print 11111111111, name
	mod = __import__(name)
	components = name.split('.')
	print components, 2222
	for comp in components[1:]:
		print comp
		mod = getattr(mod, comp)
		print mod
	return mod