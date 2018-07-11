


class HTMLContainer(object):
    '''
        HTMLContainer is the base class for HTMLGen objects. It provides the 
        hierarchy for HTML, the basics for converting HTMLGen objects into 
        strings, and a mechanism whereby calling an HTMLContainer returns another 
        HTMLContainer with additional contents and/or attributes.
        
        All contents of an HTMLContainer are flattened when the container is 
        created. That is, HTMLContainer.__init__ recursively walks through any 
        iterables it finds and adds objects one by one to the HTMLContainer's 
        content list. Exceptions are strings, Tags and Pseudotags. These are 
        treated as atoms for purposes of HTMLContainer flattening. Any object can 
        be made atomic in this way by giving it an _HTMLAtomic attribute that 
        evaluates to true.
        
        HTMLContainers can be treated as lists (hc.insert(1, x), hc.pop(3), hc[2] 
        = y, etc.).
        
        Note that HTMLContainer deals with tag attributes, even though they are 
        meaningless for TagLists. This is to consolidate code, which would 
        otherwise have to be repeated in Tag and Pseudotag.
        
        HTMLContainer is incomplete by itself. For a subclass to be useable, it 
        must implement the methods digest and wrap.
        
        def digest(self, self.x, self.y, *contents):
            return contents, self.x, self.y
        digest is called by __init__, and its purpose is to peel class-specific 
        arguments off the list of arguments passed to __init__. It must return a 
        tuple of the contents list followed by zero or more class-specific 
        arguments. The class-specific arguments will be saved by __init__, to be 
        used by __call__ to construct other HTMLContainers. Class-specific 
        arguments must come before contents, and digest must not change the order 
        of the arguments.
        
        def wrap(self, contentStr):
            return '<div>%s</div>' % contentStr
        wrap is called by __str__ to generate the actual structure of the HTML. 
        contentStr is formed by concatenating str(x) for all x in the container's 
        contents list. Subclasses must provide whatever wrapping is required.
    '''
    
    spacer = ''
    
    #Common names of attributes that interfere with reserved words in Python:
    _specialAttrs = {
        'for_' : 'for',
        'class_' : 'class',
    }
    
    _HTMLAtomic = True
    
    def _atomicOverride(self, x):
        if isinstance(x, str):
            return True
        if hasattr(x, '_HTMLAtomic') and x._HTMLAtomic:
            return True
        return False
    
    def _r_flatten(self, x):
        if self._atomicOverride(x):
            self.contents.append(x)
        else:
            try:
                it = iter(x)
            except TypeError:
                self.contents.append(x)
            else:
                for sub in it:
                    self._r_flatten(sub)
    
    def __init__(self, *args, **attrs):
        temp, *self.extraArgs = self.digest(*args)
        self.contents = []
        for obj in temp:
            self._r_flatten(obj)
        self.attrs = {self._specialAttrs.get(k, k) : v for k, v in attrs.items()}
    
    def __call__(self, *newContents, **newAttrs):
        tempAttrs = self.attrs.copy()
        tempAttrs.update(newAttrs)
        return type(self)(*(self.extraArgs + self.contents + list(newContents)), **tempAttrs)
    
    def __str__(self):
        return self.wrap(self.spacer.join(map(str, self.contents)))
    
    def __repr__(self):
        parts = [repr(arg) for arg in self.extraArgs]
        if self.attrs:
            parts.append(', '.join('%s = %s' % (k, repr(v)) for k, v in self.attrs.items()))
        ret = '%s(%s)' % (type(self).__name__, ', '.join(parts))
        if self.contents:
            ret += '(%s)' % ', '.join(map(repr, self.contents))
        return ret
    
    def __getattr__(self, name):
        try:
            return getattr(self.contents, name)
        except AttributeError:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, name))
    
    def __getitem__(self, index):
        return self.contents[index]
    
    def __setitem__(self, index, value):
        self.contents[index] = value
    
    def join(self, x):
        if self._atomicOverride(x):
            return TagList(x)
        it = iter(x)
        try:
            temp = [next(it)]
        except StopIteration:
            temp = []
        else:
            for y in it:
                temp.append(self)
                temp.append(y)
        return TagList(*temp)
    
    def __add__(self, other):
        return TagList(self, other)
    
    def __radd__(self, other):
        return TagList(other, self)



class TagList(HTMLContainer):
    '''
        tl = TagList(*contents)
        
        This is the most basic HTMLContainer. It does nothing but contain tags, 
        and doesn't have any special wrapping.
        
        TagLists can contain any object. Contents will ultimately be converted to 
        strings via str().
        
        tl(*args) -> a TagList with args appended.
        str(tl) -> the HTML you want to generate.
        
        tl.insert, tl[i]: TagLists can be treated as lists.
    '''
    
    _HTMLAtomic = False
    
    def digest(self, *contents):
        return contents,
    
    def wrap(self, contentStr):
        return contentStr
    


class Tag(HTMLContainer):
    '''
        tag = Tag(tagName, tagType, *contents, **attrs)
            tagName: the name of the tag, e.g. 'br', 'body'.
            tagType: one of Tag.NORMAL, Tag.LONE or Tag.FORCED_PAIR.
                NORMAL: The tag will produce an open tag and a close tag if there 
                    are contents (e.g. '<strong>Blah blah blah.</strong>'), or an 
                    open-and-close tag with a slash if there are no contents (e.g. 
                    '<input type="submit" />').
                LONE: The tag will produce an open-and-close tag without a slash 
                    (e.g. '<br>').
                FORCED_PAIR: The tag will produce an open tag and a close tag 
                    regardless of whether there are contents (e.g. '<script> src=
                    "http://www.somewhere.com/something.js"></script>').
            contents: the contents of the tag. The contents will be flattened down 
                to a single list. Any object can be contained within a Tag. 
                Objects will ultimately be converted to strings via str().
            attrs: attributes for the tag. There are two attributes in HTML whose 
                names conflict with Python reserved words. They can be specified 
                by adding a trailing underscore (for_, class_). Attributes given 
                the value True will be present in the open tag but not assigned 
                a value. Attributes given the value False will be absent. So, e.g. 
                str(Tag('option', Tag.NORMAL, 'Fish', selected = True)) -> 
                '<option selected>Fish</option>' but str(Tag('option', Tag.NORMAL, 
                'Fowl', selected = False) -> '<option>Fowl</option>'.

        str(tag) -> the HTML you want to generate.
        tag(x1, x2, ...) -> another Tag, with x1, x2, etc. appended to tag's 
            contents.
        tag(a1 = v1, ...) -> another Tag, now with the attribute a1 set to v1, etc.
        
        tag.insert(x), tag.append(x): treating a Tag as a list acts on the Tag's 
            contents list.
    '''
    
    NORMAL = 0
    LONE = 1
    FORCED_PAIR = 2
    
    def digest(self, *args):
        self.tagName, self.tagType, *contents = args
        if not self.tagType in [self.NORMAL, self.LONE, self.FORCED_PAIR]:
            raise ValueError('Unknown tagType %d in Tag.__init__ (%s)' % (self.tagType, self.tagName))
        return contents, self.tagName, self.tagType
    
    def _openTagGuts(self):
        temp = [self.tagName]
        for k, v in self.attrs.items():
            if v is True:
                temp.append(k)
            elif not v is False:
                temp.append('%s="%s"' % (k, str(v)))
        return ' '.join(temp)
    
    def wrap(self, contentStr):
        if self.contents or self.tagType == self.FORCED_PAIR:
            return '<%s>%s%s%s</%s>' % (self._openTagGuts(), self.spacer, contentStr, self.spacer, self.tagName)
        if self.tagType == self.LONE:
            return '<%s>' % self._openTagGuts()
        return '<%s />' % self._openTagGuts()


#################################################
#Specific Tags

import sys


_loneTags = {
    'BR' : 'br',
    'HR' : 'hr',
}
for k, v in _loneTags.items():
    sys.modules[__name__].__dict__[k] = Tag(v, Tag.LONE)

_normalTags = {
    'A' : 'a',
    'B' : 'b',
    'BODY' : 'body',
    'BUTTON' : 'button',
    'CODE' : 'code',
    'DIV' : 'div',
    'EM' : 'em',
    'EMBED' : 'embed',
    'FORM' : 'form',
    'H1' : 'h1',
    'H2' : 'h2',
    'H3' : 'h3',
    'H4' : 'h4',
    'H5' : 'h5',
    'H6' : 'h6',
    'HEAD' : 'head',
    'HTML' : 'html',
    'IFRAME' : 'iframe',
    'IMG' : 'img',
    'INPUT' : 'input',
    'I' : 'i',
    'LABEL' : 'label',
    'LINK' : 'link',
    'OPTION' : 'option',
    'P' : 'p',
    'PRE' : 'pre',
    'SEL' : 'select',
    'SPAN' : 'span',
    'STRONG' : 'strong',
    'STYLE' : 'style',
    'TITLE' : 'title',
    
    #Table stuff:
    'TABLE' : 'table',
    'TH' : 'th',
    'TR' : 'tr',
    'TD' : 'td',
    'CAPTION' : 'caption',
    'COLGROUP' : 'colgroup',
    'THEAD' : 'thead',
    'TBODY' : 'tbody',
    'TFOOT' : 'tfoot',
    
    #List stuff:
    'UL' : 'ul',
    'OL' : 'ol',
    'LI' : 'li',
    'DL' : 'dl',
    'DT' : 'dt',
    'DD' : 'dd'
}
for k, v in _normalTags.items():
    sys.modules[__name__].__dict__[k] = Tag(v, Tag.NORMAL)

_forcedPairTags = {
    'SCRIPT' : 'script',
    'TEXTAREA' : 'textarea',
    'VIDEO' : 'video',
}
for k, v in _forcedPairTags.items():
    sys.modules[__name__].__dict__[k] = Tag(v, Tag.FORCED_PAIR)




#################################################
#Utility Functions

def vif(*args):
    n = len(args)
    if n == 0:
        return ''
    if n == 1:
        return args[0]
    if args[0]:
        return args[1]
    return vif(*args[2:])

def lif(*args):
    n = len(args)
    if n == 0:
        return ''
    if n == 1:
        return args[0]()
    if args[0]():
        return args[1]()
    return lif(*args[2:])

def nbsp(n):
    return '&nbsp;' * n



#################################################
#Pseudotags

GETJQ = SCRIPT(src = 'http://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js')

class Pseudotag(HTMLContainer):
    '''
        Pseudotag is a class for wrapping a tag in a nested structure of tags. For 
        example, a complete HTML page might look like this:
        <!DOCTYPE html>
        <html>
            <head>
                <title>A Title</title>
                <link rel="stylesheet" href="blah.css" />
            </head>
            <body>
                ...
            </body>
        </html>
        and the BODY tag might be the only part we were interested in modifying. 
        In this case, we would want a PAGE. PAGE is a subclass of Pseudoclass. Its 
        heart is a BODY tag, and the rest of the page is its skeleton. Its 
        constructor takes a title and the name of a .css file as parameters, it 
        stringifies itself as the entire page, but in most other respects it 
        behaves as if it were just the BODY tag itself.
        
        Pseudotag is incomplete by itself. To be useable, subclasses must implement 
        the methods heart and skeleton, which are similar to digest and wrap in 
        HTMLContainer. Instead of returning the contents list and the wrapped 
        string, respectively, they both return HTMLContainer instances. heart 
        returns the inner Tag (the one that's being wrapped), while skeleton 
        returns the outer Tag or TagList.
    '''
    def __init__(self, *args, **attrs):
        self.inner, *self.extraArgs = self.heart(*args, **attrs)
        self.outer = self.skeleton(self.inner, *self.extraArgs)
        self.contents = self.inner.contents            #This seems like rather a hack.
        self.attrs = {self._specialAttrs.get(k, k) : v for k, v in attrs.items()}
    
    def __str__(self):
        return str(self.outer)

class LABIN(Pseudotag):
    '''
        LABIN(labelText, name, labelAttrs = {}, **kwargs)
        
        produces
        
        <label for="{name}" {labelAttrs} >{labelText}</label>
        <input name="{name}" {kwargs} />
        
        LABIN is a Pseudotag, and its heart is the INPUT tag.
    '''
    def heart(self, labelText, name, labelAttrs = {}, **kwargs):
        return INPUT(name = name, **kwargs), labelText, name, labelAttrs
    
    def skeleton(self, inner, labelText, name, labelAttrs):
        return TagList(
            LABEL(for_ = name, **labelAttrs)(labelText),
            inner
        )

class SIMPLEPAGE(Pseudotag):
    '''
        SIMPLEPAGE(*args, **kwargs)
        
        produces
        
        <!DOCTYPE html>
        <html {kwargs}>
            {args}
        </html>
        
        SIMPLEPAGE is a Pseudotag, and its heart is the HTML tag.
    '''
    def heart(self, *args, **kwargs):
        return HTML(*args, **kwargs)
    
    def skeleton(self, inner):
        return TagList(
            Tag('!DOCTYPE', Tag.LONE, html = True),
            inner
        )


class PageWrapper(Pseudotag):
    def heart(self, title, css, *args, **kwargs):
        return BODY(*args, **kwargs), title, css
    
    def skeleton(self, inner, title, css):
        return TagList(
            Tag('!DOCTYPE', Tag.LONE, html = True),
            HTML(
                self.head(title, css),
                inner
            )
        )

class PAGE(PageWrapper):
    '''
        PAGE(title, css, *args, **kwargs)
        
        produces
        
        <!DOCTYPE html>
        <html>
            <head>
                <title>{title}</title>
                <link rel="stylesheet" href="{css}" />
            </head>
            <body {kwargs}>
                {args}
            </body>
        </html>
        
        PAGE is a Pseudotag, and its heart is the BODY tag.
    '''
    def head(self, title, css):
        return HEAD(
            TITLE(title),
            vif(css, LINK(rel = 'stylesheet', href = css)),
        )

class JQPAGE(PageWrapper):
    '''
        JQPAGE(title, css, *args, **kwargs)
        
        is identical to PAGE, except that it summons jQuery by means of a script 
        tag in its HEAD. It produces
        
        <!DOCTYPE html>
        <html>
            <head>
                <title>{title}</title>
                <link rel="stylesheet" href="{css}" />
                <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script>
            </head>
            <body {kwargs}>
                {args}
            </body>
        </html>
        
        JQPAGE is a Pseudotag, and its heart is the BODY tag.
    '''
    def head(self, title, css):
        return HEAD(
            TITLE(title),
            vif(css, LINK(rel = 'stylesheet', href = css)),
            GETJQ
        )


if __name__ == '__main__':
    import random, string
    
    items = [
        ''.join(
            [random.choice(string.ascii_letters) for i in range(10)]
        )
        for j in range(10)
    ]
    
    print(str(
        JQPAGE(
            'Links Page',
            'random.css',
            H3('Links to Random Stuff'),
            (
                A(href = '%s.html' % item)(
                    IMG(src = '%s.jpg' % item, alt = 'a picture of %s' % item),
                    item
                ) + BR
                for item in items
            )
        )
    ))



