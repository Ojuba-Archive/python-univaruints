python-univaruints
==================

a pure-python implmentation of variable length unsigned integers
univaruints can be used as a serialization of integer list

idea
----

based on idea from http://code.google.com/apis/protocolbuffers/docs/encoding.html
and from UTF-8 variable length encoding of Unicode

a single integer in univaruints can be something like

    0xxx-xxxx
    10xx-xxxx xxxx-xxxx
    110x-xxxx xxxx-xxxx xxxx-xxxx 

the most significant bits till the first zero of first byte indicates the number of extra bytes

    0xxx-xxxx is 0-127
    10xx-xxxx xxxx-xxxx  is 128-16511 (as 0b1000-0000-0000-0000 => 128 and 0b1011-1111-1111-1111 => 16511)
    110x-xxxx xxxx-xxxx xxxx-xxxx is 16512-2113663 

usage
--------

it can be used like this

    import univaruints
    s=univaruints.encode([150,5,7])
    a=univaruints.decode(s)


features
--------

1. simple, fast, unit-tested and have predetermined length (from first byte)
2. it preserve order (unlike protocolbuffers) eg. can be used to sort threaded comments
3. works on single integer (encode_signle/decode_single) or list of integers
4. more compact serialization can be made for increasing lists

