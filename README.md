
<!--
  DRAFT README — structure/layout focused. Replace bracketed [placeholder] text
  and swap in real images under /gallery/hero/. Sections marked (OPTIONAL) can
  be cut if they end up redundant with docs/ pages.
-->

<div align="center">

# Making images with TiO2
### Photographic mosaics, anodized onto titanium — one color at a time
Repeated anodize → laser-ablate → re-anodize cycles on titanium sheets can produce full color 508 DPI images.  The process involves image processing, metal preparation, and repeated "dunks" in a carefully-controlled trisodium phosphate (TSP) solution with a DC voltage between 15 and 105 volts.

[![Etsy](https://img.shields.io/badge/shop-Etsy-orange)](#) 
[![License: MIT](https://img.shields.io/badge/code-MIT-blue)](#license) 
[![Discussions](https://img.shields.io/badge/community-Discussions-brightgreen)](#)

</div>

---

## Gallery preview

<table>
  <tr>
    <td width="33%">
      <img src="gallery/alien/alien.jpg" alt="alien — finished piece" width="100%">
      <p align="center"><sub><b>Finished piece (actual size 100 mm x 100 mm)</b><br>[AI generated to fit Ti palette, 508 DPI]</sub></p>
    </td>
    <td width="33%">
      <img src="gallery/alien/_index.png" alt="PNG ablation images for alien" width="100%">
      <p align="center"><sub><b>Derived from the original image by ti_mosaic_separator.py</b><br>[508 DPI preview]</sub></p>
    </td>
    <td width="33%">
      <img src="gallery/alien/alien_in_progress.jpg" alt="In progress" width="100%">
      <p align="center"><sub><b>After teal, magenta, pink, and yellow (gold) anodize dunks</b><br>[ready for ablating silver]</sub></p>
    </td>
  </tr>
  <tr>
    <td width="33%">
      <video src="https://github.com/user-attachments/assets/4446cb57-93af-415b-9d44-26bceccfb9a3" controls width="100%"></video>  
    </td>
    <td width="33%">
      <b><= Video to show the cool way the anodized pieces shimmer.</b><p> It's very hard to record and show this on the screen (looks better in real life), and the shimmer is one of the most appealing aspects of the technique. The way anodized titanium makes the appearance of colors is through interference of different wavelengths of light refracting and reflecting through the TiO2 layer created by the anodizing.  The anodizing voltage controls the thickness of the layer which in turns controls perceived color.  The shimmery effect and conjuring color out of voltage in a solution (feels like alchemy) are a lot why this process is so engaging for me.  Software, laser, chemistry, and the physics of light converge to make magic.</p>
    </td>
    <td width="33%">
      <img width="100%" alt="anodizing_rig" src="https://github.com/user-attachments/assets/b4ab74c2-aefb-4c07-ba92-6ec3ae92cb7a">
      <p align="center"><sub><b>My anodizing bath and rig, power supply, cooling and circulation systems</b><br>There is also laser with proper ventilation, a computer, and a metal prep (wet sanding) station (more details in the wiki).</sub></p>
    </td>
  </tr>
</table>

[See more examples in the gallery.](https://github.com/markjernf/titanium-images/wiki/Gallery)

---

## What this is

This repo is my effort to share what I've learned and invented about making high resolution and vibrant color images by anodizing titanium.
I am an engineer, woodworker, and maker who now crafts full-color, photorealistic images on titanium sheets by anodizing,
laser-ablating a mask of one color, re-anodizing at that color's voltage, and
repeating — up to nine times per piece. A Python script
(`ti_mosaic_separator.py`) turns a source photo into a stack of one-bit masks that when ablated and anodized in the proper order produce a color mosaic, dithering and blending the colors into a color image with excellent tonal depth.  These pieces may look like they were produced by a machine, but they are genuinely handmade.  Each requires meticulous surface preparation, multiple laser passes, and multiple separate trips to the TSP
electrolyte bath in a sophisticated hand-built anodizing rig. It's a wonderful blend of digital preparation and analog rendering and depending on how many colors are involved can take several hours to complete one piece.   

## How it works (short version)
1. Decompose the source image into per-color masks (script does this).
2. Anodize the whole sheet to the highest-voltage color — this becomes the base.
4. Laser-ablate the next color's mask; re-anodize at the next-lower voltage to add that color.
5. Repeat, descending in voltage, until all colors are laid down in a very precise 508 DPI mosaic.
6. Final pass produces a photorealistic image built from three to nine discrete anodized colors.

For lots more details, please see the Wiki.

## Why this is different

I have searched for others doing this sort of work but haven't found anyone doing exactly my combination
of anodizing and high resolution laser ablation to generate full color images.  The "dithering mosaic" separation of images into masks to ablate for different anodized colors to get a full-color image result is what's different about what I'm doing.    If others are 
doing this or if you start doing this, I'd love to hear from you!

## What I did find

* Lots of people are anodizing jewelry and other objects.
* Others are doing multiple color anodizing on pens and knife blanks, using the "anodize/ablate/anodize" strategy. [Example by wayofknife.com](https://www.wayofknife.com/the-s-house-ano/)
* [Here's a site](https://cycleschinook.com/anodizing/) advertising beautiful (and extremely sophisticated) anodizing services for bicycles by cycleschinook.com.
* Jake Wright at [Titan Prints](https://www.tiprints.com/home) developed an amazing image anodizing process using an x-y "drawing with fluid" approach (check out his [video](https://www.youtube.com/watch?v=kHKCwzJl5gQ) and [shop](https://www.tiprints.com/shop)).  He posted [more videos](https://www.instagram.com/p/DGZ5C79OKwX/) on instagram.
* [Matthew C. Martin](https://www.anodizedart.com/about) is making gorgeous art by "painting" the TiO2: [gallery](https://www.anodizedart.com/gallery).  Check out his [video](https://www.anodizedart.com/).    
* Povilas in Lithuania has the closest I found to my work.  He is [using a 60W fiber laser to anodize dots directly onto titanium](https://forum.lightburnsoftware.com/t/color-raster-images-on-metal/188901) with super cool results: [gallery](https://nothing.lt/photos/public/gallery/tqAgGPhTv77AJq2S73U2EjOD).  

As far as I've been able to determine, **combining
full color image decomposition into per-voltage ablation masks with repeated
anodize/ablate cycling to get photorealistic results at extremely high resolution** is
undocumented elsewhere. If you know of prior work I've missed, please open a
[discussion](../../discussions) — genuinely want to know.

## The struggle (it's not as easy as it looks)

These look precise because they *are* precise — but precise took months of
experimentation, isolating and dialing one variable at a time, including:

* incomplete initial metal preparation
* ablation settings too strong
* ablation settings too weak
* slightly bent corners of the sheet causing ablation to fail there
* controlling bath temperature
* proper dunk technique
* masking the back of the sheet
* DPI/pixel-mapping challenges with XCS re-dithering my PNG
* separations thatlooked right in preview and came out muddy on metal
* shadow tuning that turned out to work backwards from instinct
* forgetting steps
* not cleaning enough
* leaky cooling system diluting the bath with icy tap water
* sparks when I touched the sheet to a spot I shouldn't


## Try it yourself

[Minimal quickstart — keep short, link out for detail.]

```bash
python ti_mosaic_separator.py --input source.jpg --width-mm 94
```

Full usage, parameters, and palette calibration →
[`docs/pipeline.md`](docs/pipeline.md)

## Collaborate / get in touch

[Invite line — you specifically want to find others doing this or adjacent
work. Example seed:]

If you're doing anything in this space — pen-plotter anodizing, mask-and-dunk,
laser-direct color, or your own version of this — I'd love to hear about it
and compare notes. Open a [discussion](../../discussions) or an issue.

Finished pieces are available on [Etsy → \[shop link\]](#).
[Optional: art-show / exhibit note, e.g. "Currently showing at \[venue\]."]

## License

- **Code** (`ti_mosaic_separator.py` and related scripts): [MIT](LICENSE)
- **Images and art**: see [`LICENSE-ART.md`](LICENSE-ART.md) — [placeholder,
  e.g. CC BY-NC 4.0; not for commercial reproduction]

---

<div align="center"><sub>[optional footer, e.g. "Built and anodized by [name] — [location/workplace note if desired]"]</sub></div>

