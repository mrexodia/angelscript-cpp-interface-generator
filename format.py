
text = """
asBEHAVE_CONSTRUCT 	(Object) Constructor
asBEHAVE_DESTRUCT 	(Object) Destructor
asBEHAVE_FACTORY 	(Object) Factory
asBEHAVE_ADDREF 	(Object) AddRef
asBEHAVE_RELEASE 	(Object) Release
asBEHAVE_VALUE_CAST 	(Object) Explicit value cast operator
asBEHAVE_IMPLICIT_VALUE_CAST 	(Object) Implicit value cast operator
asBEHAVE_INDEX 	(Object) operator []
asBEHAVE_NEGATE 	(Object) operator - (Unary negate)
asBEHAVE_ASSIGNMENT 	(Object) operator =
asBEHAVE_ADD_ASSIGN 	(Object) operator +=
asBEHAVE_SUB_ASSIGN 	(Object) operator -=
asBEHAVE_MUL_ASSIGN 	(Object) operator *=
asBEHAVE_DIV_ASSIGN 	(Object) operator /=
asBEHAVE_MOD_ASSIGN 	(Object) operator =
asBEHAVE_OR_ASSIGN 	(Object) operator |=
asBEHAVE_AND_ASSIGN 	(Object) operator &=
asBEHAVE_XOR_ASSIGN 	(Object) operator ^=
asBEHAVE_SLL_ASSIGN 	(Object) operator <<=
asBEHAVE_SRL_ASSIGN 	(Object) operator >>= (Logical right shift)
asBEHAVE_SRA_ASSIGN 	(Object) operator >>>= (Arithmetic right shift)
asBEHAVE_ADD 	(Global) operator +
asBEHAVE_SUBTRACT 	(Global) operator -
asBEHAVE_MULTIPLY 	(Global) operator *
asBEHAVE_DIVIDE 	(Global) operator /
asBEHAVE_MODULO 	(Global) operator %
asBEHAVE_EQUAL 	(Global) operator ==
asBEHAVE_NOTEQUAL 	(Global) operator !=
asBEHAVE_LESSTHAN 	(Global) operator <
asBEHAVE_GREATERTHAN 	(Global) operator >
asBEHAVE_LEQUAL 	(Global) operator <=
asBEHAVE_GEQUAL 	(Global) operator >=
asBEHAVE_BIT_OR 	(Global) operator |
asBEHAVE_BIT_AND 	(Global) operator &
asBEHAVE_BIT_XOR 	(Global) operator ^
asBEHAVE_BIT_SLL 	(Global) operator <<
asBEHAVE_BIT_SRL 	(Global) operator >> (Logical right shift)
asBEHAVE_BIT_SRA 	(Global) operator >>> (Arithmetic right shift)
asBEHAVE_REF_CAST 	(Global) Explicit reference cast operator
asBEHAVE_IMPLICIT_REF_CAST 	(Global) Implicit reference cast operator
asBEHAVE_GETREFCOUNT 	(Object, GC) Get reference count
asBEHAVE_SETGCFLAG 	(Object, GC) Set GC flag
asBEHAVE_GETGCFLAG 	(Object, GC) Get GC flag
asBEHAVE_ENUMREFS 	(Object, GC) Enumerate held references
asBEHAVE_RELEASEREFS 	(Object, GC) Release all references 
"""
f=open('out.txt','w')
lines = text.split('\n')
for line in lines:
    args = line.split('\t')
    #print args
    name = args[-1]
    im=False
    newname=''
    for i in name:
        if i == '(':
            im=True
        elif i == ')' and im:
            im=False
            continue
        if im:
            continue
        newname+=i
    f.write('    \'%s\' : \'%s\', \n' % (newname.strip(), args[0].strip()))
f.close()