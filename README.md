# HTMLGen
A simple, powerful way to generate HTML from Python without interrupting the flow of Python.

## The Problem

The problem is generating HTML from inside Python. You can just construct strings with Python's native string processing machinery, but that's tremendously cumbersome. For example:
```
#The old fashioned way of doing it:
text = '<!DOCTYPE html><html><head>'
text += '<title>Links Page</title>'
text += '<link rel="stylesheet" href="random.css" />'
text += '</head><body>'
text += '<h3>Links to Random Stuff</h3>'
text += ''.join([
    '<a href="%s.html"><img src="%s.jpg" alt="a picture of %s" />%s</a><br>' % (item, item, item, item)
    for item in items
])
text += '</body></html>'

print(text)
```
The structure of the HTML being generated is completely at odds with the structure of the Python generating it, and it's very hard to see what's going on in the HTML. I admit that this isn't the best way of constructing this particular string, but in a complex page with lots of dynamic content, it doesn't get much better than this.

You could use a templating system such as that in Django, where a page is essentially stored in HTML with little bits of code inserted into it to generate the dynamic content. This is essentially the same model as PHP. It has the advantage of mostly keeping the structure of the HTML intact, but it destroys the structure of the Python (and in Django, the inserted bits of code aren't even Python anymore). If you have a programmer and an HTML guy, and your HTML guy will be scared off if he has to look at anything other than HTML, this may be the solution you want. But it's not what I, as a programmer *and* an HTML guy want.

A better solution (for people like me) is to create a function for each type of tag. The function accepts strings as arguments, concatenates them, wraps them in open and close tags and returns the result. Then calls to such functions can be nested inside one another, mirroring the structure of the HTML in Python. Tag attributes can be supplied by keyword arguments to the tag functions.

There are two problems with this solution. The first problem is that keyword arguments must come after positional arguments, and they're not visually distinct from positional arguments. The code is still hard to follow, because you have to look at the end of a tag for the tag attributes. The second problem is that it's hard to put dynamic content into an argument list for a function. You can only use expressions, not statements.

## My Solution

The solution here looks like the nested functions solution, above, but they're actually objects instead:

`tag = DIV('This is a div.')` -> creates a Tag object.

They turn into HTML when stringified via `str`:

`print(str(tag))` -> prints `"<div>This is a div.</div>"`.

Their `__init__` method accepts any number of objects of any type, which will be nested inside them:
```
print(str(
    DIV(
        'This is an outer div.',
        DIV('This is an inner div.')
    )
))
```
prints `'<div>This is an outer div.<div>This is an inner div.</div></div>'`.

They also accept keyword arguments, which become tag attributes:

`print(str(DIV(class_ = 'myClass')))` -> prints `'<div class="myClass" />'`

To solve the problem of keyword arguments coming last, tag objects are callable, and return copies of themselves with the additional attributes or contents passed in:
```
print(str(
    DIV(class_ = 'myClass')(        #Have to use class_ because class is a reserved word in Python.
        'Here is some text.'
    )
))
```
prints `'<div class="myClass">Here is some text.</div>'`. In fact, `DIV` itself is not a function or a class, but an instance of the Tag class. Note that it's possible to write `DIV('Here is some text.', class_ = 'myClass')` if you want to. It's just less clear, in my opinion, and it becomes rapidly less clear as the number and complexity of objects contained in the div increase.

To solve the problem of putting dynamic content inside argument lists, HTMLGen has several features.

Tag objects recursively flatten all their arguments into one uniform list. So you can pass a list to a Tag, and it will be as if you had added each item individually:
```
DIV(class_ = 'myClass')(
    'Here are some links:',
    BR,
    [
        A(href = url)(name)
        for name, url in myLinks.items()
    ]
)
```
produces a div containing some text, a `<br>` tag, and several anchor tags.

As for the problem of conditionals inside argument lists, you could use the normal Python syntax for conditional expressions (`consequent if condition else alternative`), but that can be cumbersome. HTMLGen provides a couple of utility functions for this, `vif` and `lif`.

`vif` works like this:

`vif()` -> '', the empty string.

`vif(a)` -> `a` if `a` evaluates to true, otherwise the empty string.

`vif(a b *rest)` -> `b` if `a` evaluates to true, otherwise `vif(*rest)`.

(The name stands for "Value If", and it comes from the special form "if" in Arc. That's probably confusing for everyone except me, and I do appologize.)

`lif` (for "Lambda If") is similar, but instead of using the values of its arguments, it calls them (with no arguments) and uses their return values. It only calls the arguments that are actually needed, so you can use this to avoid costly calculations if they won't contribute to the final HTML.

## Other Features

Tags can be added together. The result is a TagList object, which is similar to a Tag, but has no wrapping around the contents.

`print(str(SPAN(class_ = 'myClass')('Hello!') + BR))` -> prints `'<span class="myClass">Hello!</span><br>'`

Tags and TagLists can be treated as lists. They can be indexed, sliced, appended to, iterated over, etc. Tags are not, however, flattened when they're passed to the `__init__` method of another Tag.
