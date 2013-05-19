python-univaruints
==================

a pure-python implmentation of variable length unsigned integers
univaruints can be used as a serialization of integer list
which can be used to serialize more complex structures

usage
--------

this implementation offers many interfaces for convinience
but the most simple is like this (used to convert from/to strings)

    import univaruints
    s=univaruints.encode([150,5,7])
    a=univaruints.decode(s)

we also offser another interface for file-like objects

    import univaruints
    f=open('test.tmp', 'w+')
    univaruints.write(f, [150,5,7])
    f.close()
    f=open('test.tmp', 'r+')
    a=univaruints.read(f)
    f.close()


idea
----

based on idea from google's varint in its protocolbuffers http://code.google.com/apis/protocolbuffers/docs/encoding.html
and from UTF-8 variable length encoding of Unicode
I made this more compact format which is also supposed to be faster too
and have extra useful properties.

a single integer in univaruints can be something like

    0xxx-xxxx
    10xx-xxxx xxxx-xxxx
    110x-xxxx xxxx-xxxx xxxx-xxxx 

the number of leading most significant set bits (ie. till the first zero) of first byte
indicates the number of extra bytes needed to encode a single integer


    0xxx-xxxx is 0-127
    10xx-xxxx xxxx-xxxx  is 128-16511 (as 0b1000-0000-0000-0000 => 128 and 0b1011-1111-1111-1111 => 16511)
    110x-xxxx xxxx-xxxx xxxx-xxxx is 16512-2113663 


features
--------

1. simple, fast, unit-tested and have predetermined length (from first byte)
2. it preserve order (unlike protocolbuffers) eg. can be used to sort nested thread comments
3. several convinient interfaces (eg. encode_signle/decode_single)
4. more compact serialization can be made for increasing lists

Development
-----------

lookup optimization
-------------------

using pre-calculated lookup table
as you noticed 0b1000-0000-0000-0000 encodes 128 even though
the value of the payload is 0, that's because we shift the payload with sertain value
to have more compact 1-1 mapping, the values shown in table below (where i in the number of leading set bit)

    template boundary i shift
    0xxx-xxxx <=127   0 0
    10xx-xxxx <=191   1 128
    110x-xxxx <=223   2 16512
    1110-xxxx <=239   3 2113664
    1111-0xxx <=247   4 270549120
    1111-10xx <=251   5 34630287488
    1111-110x <=253   6 4432676798592
    1111-1110 <=254   7 567382630219904
    1111-1111 ==255   8 72624976668147840

to calculate the boundary (and mask to get the payload) using this fomula

    boundary = (0b11111111101111111>>i) & 255
    mask = 127>>i

the shifts sequence was calculated like this

    shifts=[0]
    s=[]
    last=0
    for i in range(9):
      boundary = (0b11111111101111111>>i) & 255
      for j in range(last, boundary+1):
        s.append(i) # on production it should be ord(i)
      last=j+1
      mask = 127>>i
      shifts.append(shifts[-1]+ 1 + (mask<<(8*i)) + ((1<<(8*i))-1) )

python-specific optimization
----------------------------

there is a room for getting faster encoding and decoding
by using the following tricks

1. have a local variable for builtin functions
2. have a local variable to do object property lookup (outside the loop)
3. use array('B', ...) to do integer/string manipulations

