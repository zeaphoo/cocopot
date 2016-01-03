#class FileUpload(fileobj, name, filename, headers=None)


Wrapper for file uploads. 

##var **content_length**



##var **content_type**



##var **headers**



##var **raw_filename**



##var **name**



##var **file**



##def **save**(destination, overwrite=False, chunk_size=65536)

Save file to disk or copy its content to an open file(-like) object.
If *destination* is a directory, `filename` is added to the
path. Existing files are not overwritten by default (IOError).

Args:

  * destination: File path, directory or file(-like) object.
  * overwrite: If True, replace existing files. (default: False)
  * chunk_size: Bytes to read at a time. (default: 64kb)
#class FormsDict(*a, **kwargs)

This `MultiDict` subclass is used to store request form data.
Additionally to the normal dict-like item access methods (which return
unmodified data as native strings), this container also supports
attribute-like access to its values. Attributes are automatically de-
or recoded to match `input_encoding` (default: 'utf8'). Missing
attributes default to an empty string. 


##var **input_encoding**



##var **recode_unicode**



##var **dict**



##def **getlist**(key)

Return a (possibly empty) list of values for a key. 

##def **pop**(key, default=object())

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
If key is not found, d is returned if given, otherwise KeyError is raised.

##def **replace**(key, value)

Replace the list of values with a single value. 

##def **append**(key, value)

Add a new value to the list of values for this key. 

##def **getall**(key)

Return a (possibly empty) list of values for a key. 

##def **iterallitems**()



##def **itervalues**()



##def **get**(key, default=None, index=0, type=None)

Return the most recent value for a key.
Args:

  * default: The default value to be returned if the key is not
       present or the type conversion fails.
  * index: An index for the list of available values.
  * type: If defined, this callable is used to cast the value
        into a specific type. Exception are suppressed and result in
        the default value to be returned.

##def **keys**()



##def **update**(*args, **kwds)

D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
In either case, this is followed by: for k, v in F.items(): D[k] = v

##def **iteritems**()



##def **popitem**()

D.popitem() -> (k, v), remove and return some (key, value) pair
as a 2-tuple; but raise KeyError if D is empty.

##def **iterkeys**()



##def **setdefault**(key, default=None)

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

##def **items**()



##def **clear**()

D.clear() -> None.  Remove all items from D.

##def **allitems**()



##def **values**()



##def **getone**(key, default=None, index=0, type=None)

Return the most recent value for a key.
Args:

  * default: The default value to be returned if the key is not
       present or the type conversion fails.
  * index: An index for the list of available values.
  * type: If defined, this callable is used to cast the value
        into a specific type. Exception are suppressed and result in
        the default value to be returned.

##def **getunicode**(name, default=None, encoding=None)

Return the value as a unicode string, or the default. 
#class HeaderDict(*a, **ka)

A case-insensitive version of `MultiDict` that defaults to
replace the old value instead of appending it. 


##var **dict**



##def **getlist**(key)

Return a (possibly empty) list of values for a key. 

##def **setdefault**(key, default=None)

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

##def **get**(key, default=None, index=0)



##def **keys**()



##def **items**()



##def **clear**()

D.clear() -> None.  Remove all items from D.

##def **getall**(key)



##def **update**(*args, **kwds)

D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
In either case, this is followed by: for k, v in F.items(): D[k] = v

##def **pop**(key, default=object())

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
If key is not found, d is returned if given, otherwise KeyError is raised.

##def **replace**(key, value)



##def **iterallitems**()



##def **values**()



##def **getone**(key, default=None, index=0, type=None)

Return the most recent value for a key.
Args:

  * default: The default value to be returned if the key is not
       present or the type conversion fails.
  * index: An index for the list of available values.
  * type: If defined, this callable is used to cast the value
        into a specific type. Exception are suppressed and result in
        the default value to be returned.

##def **itervalues**()



##def **iteritems**()



##def **popitem**()

D.popitem() -> (k, v), remove and return some (key, value) pair
as a 2-tuple; but raise KeyError if D is empty.

##def **allitems**()



##def **iterkeys**()



##def **append**(key, value)


#class HeaderProperty(name, reader=None, writer=str, default='')



#class MultiDict(*a, **kwargs)

This dict stores multiple values per key, but behaves exactly like a
normal dict in that it returns only the newest value for any given key.
There are special methods available to access the full list of values.

Basic Usage:

    >>> d = MultiDict([('a', 'b'), ('a', 'c')])
    >>> d
    MultiDict([('a', 'b'), ('a', 'c')])
    >>> d['a']
    'b'
    >>> d.getlist('a')
    ['b', 'c']
    >>> 'a' in d
    True


##var **dict**



##def **getlist**(key)

Return a (possibly empty) list of values for a key. 

##def **setdefault**(key, default=None)

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

##def **get**(key, default=None, index=0, type=None)

Return the most recent value for a key.
Args:

  * default: The default value to be returned if the key is not
       present or the type conversion fails.
  * index: An index for the list of available values.
  * type: If defined, this callable is used to cast the value
        into a specific type. Exception are suppressed and result in
        the default value to be returned.

##def **keys**()



##def **items**()



##def **clear**()

D.clear() -> None.  Remove all items from D.

##def **getall**(key)

Return a (possibly empty) list of values for a key. 

##def **update**(*args, **kwds)

D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
In either case, this is followed by: for k, v in F.items(): D[k] = v

##def **pop**(key, default=object())

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
If key is not found, d is returned if given, otherwise KeyError is raised.

##def **replace**(key, value)

Replace the list of values with a single value. 

##def **iterallitems**()



##def **values**()



##def **iterkeys**()



##def **getone**(key, default=None, index=0, type=None)

Return the most recent value for a key.
Args:

  * default: The default value to be returned if the key is not
       present or the type conversion fails.
  * index: An index for the list of available values.
  * type: If defined, this callable is used to cast the value
        into a specific type. Exception are suppressed and result in
        the default value to be returned.

##def **iteritems**()



##def **popitem**()

D.popitem() -> (k, v), remove and return some (key, value) pair
as a 2-tuple; but raise KeyError if D is empty.

##def **allitems**()



##def **itervalues**()



##def **append**(key, value)

Add a new value to the list of values for this key. 
#class WSGIHeaders(environ)

This dict-like class wraps a WSGI environ dict and provides convenient
access to HTTP_* fields. Keys and values are native strings
(2.x bytes or 3.x unicode) and keys are case-insensitive. If the WSGI
environment contains non-native string values, these are de- or encoded
using a lossless 'latin1' character set.
The API will remain stable even on changes to the relevant PEPs.
Currently PEP 333, 444 and 3333 are supported. (PEP 444 is the only one
that uses non-native strings.)


##var **cgikeys**



##var **environ**



##def **setdefault**(key, default=None)

D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D

##def **get**(key, default=None)

D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None.

##def **keys**()



##def **items**()

D.items() -> list of D's (key, value) pairs, as 2-tuples

##def **clear**()

D.clear() -> None.  Remove all items from D.

##def **popitem**()

D.popitem() -> (k, v), remove and return some (key, value) pair
as a 2-tuple; but raise KeyError if D is empty.

##def **update**(*args, **kwds)

D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
In either case, this is followed by: for k, v in F.items(): D[k] = v

##def **pop**(key, default=object())

D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
If key is not found, d is returned if given, otherwise KeyError is raised.

##def **raw**(key, default=None)

Return the header value as is (may be bytes or unicode). 

##def **values**()

D.values() -> list of D's values

##def **itervalues**()

D.itervalues() -> an iterator over the values of D

##def **iteritems**()

D.iteritems() -> an iterator over the (key, value) items of D

##def **iterkeys**()

D.iterkeys() -> an iterator over the keys of D