# 👁 Retina

Retina takes an image and a thumbnail alias and generates a dict with resized images. So if your `easy_thumbnails`
alias looks something like this `'portrait': {'size': (150, 200)}` you'll get the resized version of the original image
plus a retina version of it.

```python  
image = File(user.profile_image).srcset('portrait')

# image holds now the following dict:
{
  'urls': {
    'default': [
      'path/to/images/profile_image__150x200.jpg',
      'path/to/images/profile_image__300x400.jpg',
    ]
  },
  'alt': 'John Doe',
}
```

## Installation 
First, install the latest release:

    $ pip install retina

Register the adapters you want to use somewhere at boot:

```python  
from filer.models import Image as FilerImage
from filer.models import File as FilerFile

from retina.adapters.filer import FilerImageAdapter, FilerFileAdapter
from retina import manager

manager.update_adapters({
  FilerImage: FilerImageAdapter,
  FilerFile: FilerFileAdapter,
})
```

Or if you're using `django` with `django-filer` (which is the use-case Retina was developed for) this is even easier:

```python  
from retina import manager

manager.load_default_adapters()
```

## Usage

Initiate the `retina.File` class with a `django-filer` `File` or `Image` model and call the `srcset` method with a `easy_thumbnails` alias as parameter on it. This will always return a dict with a `urls` and `alt` key. Where `urls` is again a dict of different sizes (`default` being the default if nothing else specified) and `alt` is just a string containing the alt text for the image. Retina tries to get the alt text by accessing any of the following properties on the `filer.Image` model: `default_alt_text`, `name`, `original_filename`

### Basic

```python  
image = File(user.profile_image).srcset('portrait')

{
  'urls': {
    'default': [
      'path/to/images/profile_image__150x200.jpg',
      'path/to/images/profile_image__300x400.jpg',
    ]
  },
  'alt': 'John Doe',
}
```

### Density
You can chain an additional density method to get a @3, @4, e.t.c version of the source image.

```python  
image = File(user.profile_image).density(3).srcset('portrait')

{
  'urls': {
    'default': [
      'path/to/images/profile_image__150x200.jpg',
      'path/to/images/profile_image__300x400.jpg',
      'path/to/images/profile_image__450x600.jpg',
    ]
  },
  'alt': 'John Doe',
}
```

### Sizes
If you're website needs different image dimensions, say on mobile than on desktop, you can do that as well:

```python 
THUMBNAIL_ALIASES = {
  '': {
    'portrait_sm': {'size': (100, 100)},
    'portrait_xl': {'size': (150, 200)},
    }
},
    
image = File(user.profile_image).srcset('portrait', ['sm', 'xl'])

{
  'urls': {
    'sm': [
      'path/to/images/profile_image__100x100.jpg',
      'path/to/images/profile_image__200x200.jpg',
    ],
    'xl': [
      'path/to/images/profile_image__150x200.jpg',
      'path/to/images/profile_image__300x400.jpg',
    ]
  },
  'alt': 'John Doe',
}
```

Notice how the alias is now a combination of `portrait` + `_` + `[size]`

### Additional Data
Pass in any arbitary additional data to the returned dict:

```python     
image = File(user.profile_image)).additional(foo='bar', bar='baz').srcset('portrait')

{
  'urls': {
    'default': [
      'path/to/images/profile_image__150x200.jpg',
      'path/to/images/profile_image__300x400.jpg',
    ],
  },
  'foo': 'bar',
  'bar': 'baz',
  'alt': 'John Doe',
}
```

Notice how the alias is now a combination of `portrait` + `_` + `[size]`


## Adapters
Retina uses the concept of adapters. Each adapter implements a set of methods that define how an image instance (whatever it may be) should be resized. Retina ships with two adapters out of the box: `FilerImageAdapter` and `FilerFileAdapter`. This means, that if you followed the installation steps above you can pass in any `django-filer` `File` or `Image` model and it will output you resized versions of given file (if resizable at all). 

You're free two write your own adapters and register them on the manager via the `update_adapters` method. Just pass in a dict where the key is a python `type` (like str, dict or any other object) and the value is your adapter.
