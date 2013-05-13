# -*- coding: UTF-8 -*-
"""
univaruints is a serialization of integer list
Copyright © 2009-2013, Muayyad Alsadi <alsadi@ojuba.org>

univaruints is a serialization of integer list
based on idea from http://code.google.com/apis/protocolbuffers/docs/encoding.html
and from UTF-8 variable length encoding of Unicode

but unlike protocolbuffers it preserve order by saving most significant first

in this implementation a single univaruint can be something like

0xxx-xxxx
10xx-xxxx xxxx-xxxx
110x-xxxx xxxx-xxxx xxxx-xxxx 

the most significant bits till the first zero indicates the number of extra bytes

0xxx-xxxx is 0-127

10xx-xxxx xxxx-xxxx  is 128-16511 (as 0b1000-0000-0000-0000 => 128 and 0b1011-1111-1111-1111 => 16511)

110x-xxxx xxxx-xxxx xxxx-xxxx is 16512-2113663 

and so on

use it like this

s=univaruints.encode([150,5,7])
a=univaruints.decode(s)

there are versions for single integer or for mor compact encoding of incremental lists

this implementation is unit-tested (by running this module)

this implementation uses precalculated lookup-table

template boundary i shift
0xxx-xxxx <=127   0 0
10xx-xxxx <=191   1 128
110x-xxxx <=223   2 16512
1110-xxxx <=239   3
1111-0xxx <=247   4
1111-10xx <=251   5
1111-110x <=253   6
1111-1110 <=254   7
1111-1111 ==255   8

it was constructed using

boundary = (0b11111111101111111>>i) & 255
mask = 127>>i

the shifts sequence was generated using this code

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
"""

import struct, bisect
int64=struct.Struct('>Q')
shifts=[0, 128, 16512, 2113664, 270549120, 34630287488, 4432676798592, 567382630219904, 72624976668147840]
shifts2=shifts[2:]
n_by_chr='\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x04\x04\x04\x04\x04\x04\x04\x04\x05\x05\x05\x05\x06\x06\x07\x08'

def decode_single(s):
  """
  return number of bytes consumed and the decoded value
  """   
  o=ord(s[0])
  if o<128: return 1, o
  n_ch=n_by_chr[o]
  n=ord(n_ch)
  mask=127>>n
  return n+1, shifts[n] + (((o & mask)<< (n<<3)) | ( (int64.unpack(('\0'*(8-n))+s[1:n+1]))[0] ))

def decode(s):
  "return a generator that yields all decoded integers"
  offset=0
  while offset<len(s):
    o=ord(s[offset])
    offset+=1
    if o<128: yield o # just an optimization
    else:
      n_ch=n_by_chr[o]
      n=ord(n_ch)
      mask=127>>n
      yield shifts[n] + (((o & mask)<< (n<<3)) | ( (int64.unpack(('\0'*(8-n))+s[offset:offset+n]))[0] ))
      offset+=n

def encode_single(v):
    if v<128: return chr(v)
    n=bisect.bisect_right(shifts2, v)+1
    offset=shifts[n]
    v-=offset
    return chr(((0b1111111100000000>>n) & 255) | ( (127>>n) & (v>>(n<<3)) )) + int64.pack(v)[8-n:]

def encode_single_alt(v):
    if v<128: return chr(v) # just an optimization
    offset=128
    m=0
    # enumerate was slower
    #for i,m in enumerate(shifts2):
    for i in shifts2: # although we can use bisect, but we only got 8 elements
        n=m+1
        if v<i:
            v-=offset
            msb=((0b1111111100000000>>n) & 255) | ( (127>>n) & (v>>(n<<3)) )
            p=int64.pack(v)
            return chr(msb) + p[8-n:]
        offset=i
        m+=1
    #m+=1 # if enumerate is used uncomment this line
    v-=offset
    n=m+1
    msb=((0b1111111100000000>>n) & 255) | ( (127>>n) & (v>>(n<<3)) )
    p=int64.pack(v)
    return chr(msb) + p[8-n:]

def encode(a):
    return "".join(map(encode_single, a))

def incremental_encode_list(a, unique=1, last=0):
  if unique!=1 and unique!=0: raise ValueError
  last-=unique
  for i in a:
    if i<last+unique: raise ValueError
    yield i-last-unique
    last=i

def incremental_decode_list(a, unique=1, last=0):
  if unique!=1 and unique!=0: raise ValueError
  last-=unique
  for i in a:
    j=i+last+unique
    yield j
    last=j

def incremental_encode(a, unique=1, last=0):
  return encode(incremental_encode_list(a, unique, last))

def incremental_decode(s, unique=1, last=0):
  return incremental_decode_list(decode(s), unique, last)

if __name__ == "__main__":
  import time, itertools, random
  boundary=[(i-1,i,i+1) for i in shifts[1:]]
  boundary=list(itertools.chain(*boundary))
  boundary.insert(0,0)
  print "simple unit tests..."
  for i in [0,1,100,200,300,500,1000,10000]:
    print 'before dec:', i, ', hex:', hex(i), ', bin:', bin(i)
    e=encode_single(i)
    print 'after len:',len(e), ', str:', repr(e)
    assert i == decode_single(encode_single(i))[1]
  print "boundary unit tests..."
  for i in boundary:
    print 'before dec:', i, ', hex:', hex(i), ', bin:', bin(i)
    e=encode_single(i)
    print 'after len:',len(e), ', str:', repr(e)
    assert i == decode_single(encode_single(i))[1]
  assert boundary == list(decode(encode(boundary)))
  assert boundary == list(incremental_decode(incremental_encode(boundary, unique=0), unique=0))
  assert boundary == list(incremental_decode(incremental_encode(boundary, unique=1), unique=1))
  print "random unit tests..."
  l=[random.randint(0, 5000000) for i in range(1000)]
  s=encode(l)
  l2=list(decode(s))
  assert l2==l
  ll=0
  l=[0]
  for i in range(1000):
    ll+=random.randint(0, 5000000)
    l.append(ll)
  l2=list(incremental_decode(incremental_encode(l, unique=0), unique=0))
  assert l2==l

  ll=0
  l=[0]
  for i in range(1000):
    ll+=random.randint(1, 5000000)
    l.append(ll)
  l2=list(incremental_decode(incremental_encode(l, unique=1), unique=1))
  assert l2==l

  print "pass"
  print "performance tests"
  q=struct.Struct('>Q')
  pack=lambda l: ''.join(itertools.imap(lambda i: q.pack(i), l))
  def unpack(s):
      for i in range(0,len(s),8):
          yield q.unpack(s[i:i+8])[0]
  t1=time.time()
  for i in range(1000): unpack(pack(boundary))
  t2=time.time()
  delta_pack=t2-t1
  print 'struct-based done in ', delta_pack
  t1=time.time()
  for i in range(1000): decode(encode(boundary))
  t2=time.time()
  delta_our=t2-t1
  print 'we are done in ', delta_our
  t1=time.time()
  for i in range(1000): encode(boundary)
  t2=time.time()
  delta_our=t2-t1
  print 'we are done in encoding in ', delta_our
  e=encode(boundary)
  t1=time.time()
  for i in range(1000): decode(e)
  t2=time.time()
  delta_our=t2-t1
  print 'we are done in decoding in ', delta_our

