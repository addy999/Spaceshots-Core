# Brython build of library for use in JS

Built with [brython-cli](https://brython.info/static_doc/en/brython-packages.html).

To get started, use the following scripts in your html:

```html
<!--> Loads JS implementation of Python -->
<script async="async" src="https://cdn.jsdelivr.net/npm/brython@3.9.0/brython.min.js">
</script>

<!--> Loads all standard libraries of Python (time, math, etc...)  -->
<script async="async" src="https://cdn.jsdelivr.net/npm/brython@3.9.0/brython_stdlib.js">
</script>

<!--> Loads spaceshots library -->
<script async="async" src="url to spaceshots.brython.js">
</script>

<!--> Attaches spaceshots API to the window object for use in javascript code -->
<script type="text/python3">
    from browser import window
    import spaceshots
    window.game = spaceshots.api
</script>
```

Then, to attach the api to the window object, in your JS code, type:
```js
brython()
```
