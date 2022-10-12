from num2words import num2words
import numpy as np
import re
import json
from shapely.geometry.polygon import Polygon
from shapely.affinity import scale
from PIL import Image, ImageDraw

def containsNumber(value):
    for character in value:
        if character.isdigit():
            return True
    return False
    
def creativity(intensity):
    print(intensity)
    if(intensity == 'Low'):
        top_p = 0.95
        top_k = 10
    elif(intensity == 'Medium'):
        top_p = 0.9
        top_k = 50
    if(intensity == 'High'):
        top_p = 0.85
        top_k = 100
    return top_p, top_k

housegan_labels = {"living_room": 1, "kitchen": 2, "bedroom": 3, "bathroom": 4, "missing": 5, "closet": 6, 
                         "balcony": 7, "corridor": 8, "dining_room": 9, "laundry_room": 10}

architext_colors = [[0, 0, 0], [249, 222, 182], [195, 209, 217], [250, 120, 128], [126, 202, 235], [0, 210, 239],
                    [190, 0, 198], [255, 255, 255], [19, 30, 51], [17, 33, 58], [132, 151, 246], [197, 203, 159], [6, 53, 17], ]

regex = re.compile(".*?\((.*?)\)")


def draw_polygons(polygons, colors, im_size=(512, 512), fpath=None):
    image = Image.new("RGBA", im_size, color="white")
    draw = ImageDraw.Draw(image)
    for poly, color, in zip(polygons, colors):
        #get initial polygon coordinates
        xy = poly.exterior.xy
        coords = np.dstack((xy[1], xy[0])).flatten()
        # draw it on canvas, with the appropriate colors
        draw.polygon(list(coords), fill=(0, 0, 0))
        #get inner polygon coordinates
        small_poly = poly.buffer(-1, resolution=32, cap_style=2, join_style=2, mitre_limit=5.0)
        if small_poly.geom_type == 'MultiPolygon':
            mycoordslist = [list(x.exterior.coords) for x in small_poly]
            for coord in mycoordslist:
                coords = np.dstack((np.array(coord)[:,1], np.array(coord)[:, 0])).flatten()
                draw.polygon(list(coords), fill=tuple(color)) 
        elif poly.geom_type == 'Polygon':
            #get inner polygon coordinates
            xy2 = small_poly.exterior.xy
            coords2 = np.dstack((xy2[1], xy2[0])).flatten()
            # draw it on canvas, with the appropriate colors
            draw.polygon(list(coords2), fill=tuple(color))
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    if(fpath):
        image.save(fpath, quality=100, subsampling=0)
    return draw, image

def prompt_to_layout(finetuned, tokenizer, device, user_prompt, intensity, fpath=None):
    top_p, top_k = creativity(intensity)
    model_prompt = '[User prompt] {} [Layout]'.format(user_prompt)

    if(containsNumber(user_prompt) == True):
        spaced_prompt = user_prompt.split(' ')
        new_prompt = ' '.join([word if word.isdigit() == False else num2words(int(word)).lower() for word in spaced_prompt])
        model_prompt = '[User prompt] {} [Layout]'.format(new_prompt)

    input_ids = tokenizer(model_prompt, return_tensors='pt').to(device)
    output = finetuned.generate(**input_ids, do_sample=True, top_p=top_p, top_k=top_k, 
                                eos_token_id=50256, max_length=400)
    output = tokenizer.batch_decode(output, skip_special_tokens=True)
    layout = output[0].split('[User prompt]')[1].split('[Layout] ')[1].split(', ')
    spaces = [txt.split(':')[0] for txt in layout]
    coords = [txt.split(':')[1].rstrip() for txt in layout]
    coordinates = [re.findall(regex, coord) for coord in coords]
    
    num_coords = []
    for coord in coordinates:
        temp = []
        for xy in coord:
            numbers = xy.split(',')
            temp.append(tuple([int(num)/14.2 for num in numbers]))
        num_coords.append(temp)
        
    new_spaces = []
    for i, v in enumerate(spaces):
        totalcount = spaces.count(v)
        count = spaces[:i].count(v)
        new_spaces.append(v + str(count + 1) if totalcount > 1 else v)
        
    out_dict = dict(zip(new_spaces, num_coords))
    out_dict = json.dumps(out_dict)
       
    polygons = []
    for coord in coordinates:
        polygons.append([point.split(',') for point in coord])  
    geom = []
    for poly in polygons:
        scaled_poly = scale(Polygon(np.array(poly, dtype=int)), xfact=2, yfact=2, origin=(0,0))
        geom.append(scaled_poly)  
    
    spaces = [space[:-1] if space[:-1] in housegan_labels else space for space in spaces]

    colors = [architext_colors[housegan_labels[space]] for space in spaces]
    _, im = draw_polygons(geom, colors, fpath=fpath)
    legend = Image.open("examples/architext/labels.png")
    imgs_comb = np.vstack([im, legend])
    imgs_comb = Image.fromarray(imgs_comb)
    return imgs_comb, out_dict 
     
