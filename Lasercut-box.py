#!/usr/bin/env/python
'''
Copyright (C)2011 Mark Schafer <neon.mark(a)gmaildotcom>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This    program    is    distributed in the    hope    that    it    will    be    useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
'''

# Build a tabbed box for lasercutting with tight fit, and minimal material use options.
# User defines:
# - internal or external dimensions,
# - number of tabs,
# - amount lost to laser (kerf),
# - include corner cubes or not,
# - dimples, or perfect fit (accounting for kerf).
#   If zero kerf - will    be    perfectly    packed    for minimal    laser    cuts    and    material    size.

### Todo
#  add option to pack multiple boxes (if zero kerf) - new tab maybe?
#  add option for little circles at sharp corners for acrylic
#  annotations: - add overlap value as markup - Ponoko annotation color
#  choose colours from a dictionary

### Versions
#  0.1 February 2011 - basic lasercut box with dimples etc
#  0.2 changes to unittouu for Inkscape 0.91

__version__ = "0.1"

import inkex, simplestyle
#from math import *
from simplepath import *
import sys

class LasercutBox(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("-i", "--int_ext",
                        action="store", type="inkbool",
                        dest="int_ext", default=False,
                        help="Are the Dimensions for External or Internal sizing.")
        self.OptionParser.add_option("-x", "--width",
                        action="store", type="float",
                        dest="width", default=50.0,
                        help="The Box Width - in the X dimension")
        self.OptionParser.add_option("-y", "--height",
                        action="store", type="float",
                        dest="height", default=30.0,
                        help="The Box Height - in the Y dimension")
        self.OptionParser.add_option("-z", "--depth",
                        action="store", type="float",
                        dest="depth", default=15.0,
                        help="The Box Depth - in the Z dimension")
        self.OptionParser.add_option("-t", "--thickness",
                        action="store", type="float",
                        dest="thickness", default=3.0,
                        help="Material Thickness - critical to know")
        self.OptionParser.add_option("-u", "--units",
                        action="store", type="string",
                        dest="units", default="cm",
                        help="The unit of the box dimensions")
        self.OptionParser.add_option("-c", "--corners",
                        action="store", type="inkbool",
                        dest="corners", default=True,
                        help="The corner cubes can be removed for a different look")
        self.OptionParser.add_option("-p", "--ntab_W",
                        action="store", type="int",
                        dest="ntab_W", default=11,
                        help="Number of tabs in Width")
        self.OptionParser.add_option("-q", "--ntab_H",
                        action="store", type="int",
                        dest="ntab_H", default=11,
                        help="Number of tabs in Height")
        self.OptionParser.add_option("-r", "--ntab_D",
                        action="store", type="int",
                        dest="ntab_D", default=6,
                        help="Number of tabs in Depth")
        self.OptionParser.add_option("-k", "--kerf_size",
                        action="store", type="float",
                        dest="kerf_size", default=0.0,
                        help="Kerf size - amount lost to laser for this material. 0 = loose fit")
        self.OptionParser.add_option("-d", "--dimples",
                        action="store", type="inkbool",
                        dest="dimples", default=False,
                        help="Add dimples for press fitting wooden materials")
        self.OptionParser.add_option("-s", "--dstyle",
                        action="store", type="inkbool",
                        dest="dstyle", default=False,
                        help="Dimples can be triangles(cheaper) or half rounds(better)")
        self.OptionParser.add_option("-g", "--linewidth",
                        action="store", type="inkbool",
                        dest="linewidth", default=False,
                        help="Use the kerf value as the drawn line width")
        self.OptionParser.add_option("-j", "--annotation",
                        action="store", type="inkbool",
                        dest="annotation", default=True,
                        help="Show Kerf value as annotation")
        #dummy for the doc tab - which is named
        self.OptionParser.add_option("--tab",
                        action="store", type="string", 
                        dest="tab", default="use",
                        help="The selected UI-tab when OK was pressed")
        #internal useful variables
        self.stroke_width  = 0.1 #default for visiblity
        self.line_style = {'stroke':          '#0000FF', # Ponoko blue
                           'fill':            'none',
                           'stroke-width':    self.stroke_width,
                           'stroke-linecap':  'butt',
                           'stroke-linejoin': 'miter'}

    def annotation(self, x, y, text):
        """ Draw text at this location
         - change to path
         - use annotation color        """
        pass
            
            
    def thickness_line(self, dimple, vert_horiz, pos_neg):
        """ called to draw dimples (also draws simple lines if no dimple)
             - pos_neg is 1, -1 for direction
             - vert_horiz is v or h                """
        if dimple and self.kerf > 0.0: # we need a dimple
            # size is radius = kerf
            # short line, half circle, short line
            #[ 'C', [x1,y1, x2,y2, x,y] ]  x1 is first handle, x2 is second
            lines = []
            radius = self.kerf
            if self.thick - 2 * radius < 0.2:  # correct for large dimples(kerf) on small thicknesses
                radius = (self.thick - 0.2) / 2
                short = 0.1
            else:
                short = self.thick/2 - radius
            if vert_horiz == 'v': # vertical line
                # first short line
                lines.append(['v', [0, pos_neg*short]])
                # half circle
                if pos_neg == 1: # only the DH_sides need reversed tabs to interlock
                    if self.dimple_tri:
                        lines.append(['l', [radius, pos_neg*radius]])
                        lines.append(['l', [-radius, pos_neg*radius]])
                    else:
                        lines.append(['c', [radius, 0, radius, pos_neg*2*radius, 0, pos_neg*2*radius]])                
                else:
                    if self.dimple_tri:
                        lines.append(['l', [-radius, pos_neg*radius]])
                        lines.append(['l', [radius, pos_neg*radius]])
                    else:
                        lines.append(['c', [-radius, 0, -radius, pos_neg*2*radius, 0, pos_neg*2*radius]])
                # last short line
                lines.append(['v', [0, pos_neg*short]])
            else: # horizontal line
                # first short line
                lines.append(['h', [pos_neg*short, 0]])
                # half circle
                if self.dimple_tri:
                    lines.append(['l', [pos_neg*radius, radius]])
                    lines.append(['l', [pos_neg*radius, -radius]])
                else:
                    lines.append(['c', [0, radius, pos_neg*2*radius, radius, pos_neg*2*radius, 0]])
                # last short line
                lines.append(['h', [pos_neg*short, 0]])
            return lines
        
        # No dimple - so much easier
        else: # return a straight v or h line same as thickness
            if vert_horiz == 'v':
                return [ ['v', [0, pos_neg*self.thick]] ]
            else:
                return [ ['h', [pos_neg*self.thick, 0]] ]


    def draw_WH_lid(self, startx, starty, masktop=False):
        """ Return an SVG path for the top or bottom of box
             - the Width * Height dimension                    """
        line_path = []
        line_path.append(['M', [startx, starty]])
        # top row of tabs
        if masktop and self.kerf ==0.0: # don't draw top for packing with no extra cuts
            line_path.append(['m', [self.boxW, 0]])
        else:
            for i in range(self.Wtabs):
                line_path.append(['h', [self.boxW/self.Wtabs/4 - self.pf/2, 0]])
                #line_path.append(['v', [0, -thick]])  # replaced with dimpled version
                for l in self.thickness_line(self.dimple, 'v', -1):
                    line_path.append(l)
                line_path.append(['h', [self.boxW/self.Wtabs/2 + self.pf, 0]])
                line_path.append(['v', [0, self.thick]])
                line_path.append(['h', [self.boxW/self.Wtabs/4 - self.pf/2, 0]])
        # right hand vertical drop
        for i in range(self.Htabs):
            line_path.append(['v', [0, self.boxH/self.Htabs/4 - self.pf/2]])
            line_path.append(['h', [self.thick, 0]])
            line_path.append(['v', [0, self.boxH/self.Htabs/2 + self.pf]])
            #line_path.append(['h', [-thick, 0]]) # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [0, self.boxH/self.Htabs/4 - self.pf/2]])
        # bottom row (in reverse)
        for i in range(self.Wtabs):
            line_path.append(['h', [-self.boxW/self.Wtabs/4 + self.pf/2, 0]])
            line_path.append(['v', [0, self.thick]])
            line_path.append(['h', [-self.boxW/self.Wtabs/2 - self.pf, 0]])
            #line_path.append(['v', [0, -thick]])    # replaced    with    dimpled    version
            for l in self.thickness_line(self.dimple, 'v', -1):
                line_path.append(l)
            line_path.append(['h', [-self.boxW/self.Wtabs/4 + self.pf/2, 0]])
        # up the left hand side
        for i in range(self.Htabs):
            line_path.append(['v', [0, -self.boxH/self.Htabs/4 + self.pf/2]])
            #line_path.append(['h', [-thick, 0]]) # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [0, -self.boxH/self.Htabs/2 - self.pf]])
            line_path.append(['h', [self.thick, 0]])
            line_path.append(['v', [0, -self.boxH/self.Htabs/4 + self.pf/2]])
        return line_path


    def draw_WD_side(self, startx, starty, mask=False, corners=True):
        """ Return an SVG path for the long side of box
             - the Width * Depth dimension                    """
        # Draw side of the box (placed below the lid)
        line_path = []
        # top row of tabs
        if corners:
            line_path.append(['M', [startx - self.thick, starty]])
            line_path.append(['v', [0, -self.thick]])
            line_path.append(['h', [self.thick, 0]])
        else:
            line_path.append(['M', [startx, starty]])
            line_path.append(['v', [0, -self.thick]])
        #
        if self.kerf > 0.0: # if fit perfectly - don't draw double line
            for i in range(self.Wtabs):
                line_path.append(['h', [self.boxW/self.Wtabs/4 + self.pf/2, 0]])
                line_path.append(['v', [0, self.thick]])
                line_path.append(['h', [self.boxW/self.Wtabs/2 - self.pf, 0]])
                #line_path.append(['v', [0, -thick]]) # replaced with dimpled version
                for l in self.thickness_line(self.dimple, 'v', -1):
                    line_path.append(l)
                line_path.append(['h', [self.boxW/self.Wtabs/4 + self.pf/2, 0]])
            if corners: line_path.append(['h', [self.thick, 0]])
        else: # move to skipped drawn lines
            if corners:    
                line_path.append(['m', [self.boxW + self.thick, 0]])
            else:
                line_path.append(['m', [self.boxW, 0]])
        #
        line_path.append(['v', [0, self.thick]])
        if not corners: line_path.append(['h', [self.thick, 0]])
        # RHS
        for i in range(self.Dtabs):
            line_path.append(['v', [0, self.boxD/self.Dtabs/4 + self.pf/2]])
            #line_path.append(['h', [-thick, 0]])  # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [0, self.boxD/self.Dtabs/2 - self.pf]])
            line_path.append(['h', [self.thick, 0]])
            line_path.append(['v', [0, self.boxD/self.Dtabs/4 + self.pf/2]])
        #
        if corners:
            line_path.append(['v', [0, self.thick]])
            line_path.append(['h', [-self.thick, 0]])
        else:
            line_path.append(['h', [-self.thick, 0]])
            line_path.append(['v', [0, self.thick]])
        # base
        for i in range(self.Wtabs):
            line_path.append(['h', [-self.boxW/self.Wtabs/4 - self.pf/2, 0]])
            #line_path.append(['v', [0, -thick]]) # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'v', -1):
                line_path.append(l)
            line_path.append(['h', [-self.boxW/self.Wtabs/2 + self.pf, 0]])
            line_path.append(['v', [0, self.thick]])
            line_path.append(['h', [-self.boxW/self.Wtabs/4 - self.pf/2, 0]])
        #
        if corners:
            line_path.append(['h', [-self.thick, 0]])
            line_path.append(['v', [0, -self.thick]])
        else:
            line_path.append(['v', [0, -self.thick]])
            line_path.append(['h', [-self.thick, 0]])
        # LHS
        for i in range(self.Dtabs):
            line_path.append(['v', [0, -self.boxD/self.Dtabs/4 - self.pf/2]])
            line_path.append(['h', [self.thick, 0]])
            line_path.append(['v', [0, -self.boxD/self.Dtabs/2 + self.pf]])
            #line_path.append(['h', [-thick, 0]])    # replaced    with    dimpled    version
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [0, -self.boxD/self.Dtabs/4 - self.pf/2]])
        #
        if not corners: line_path.append(['h', [self.thick, 0]])
        return line_path


    def draw_HD_side(self, startx, starty, corners, mask=False):
        """ Return an SVG path for the short side of box
             - the Height * Depth dimension                    """
        line_path = []
        # top row of tabs
        line_path.append(['M', [startx, starty]])
        if not(mask and corners and self.kerf == 0.0):
            line_path.append(['h', [self.thick, 0]])
        else:
            line_path.append(['m', [self.thick, 0]])
        for i in range(self.Dtabs):
            line_path.append(['h', [self.boxD/self.Dtabs/4 - self.pf/2, 0]])
            line_path.append(['v', [0, -self.thick]])
            line_path.append(['h', [self.boxD/self.Dtabs/2 + self.pf, 0]])
            #line_path.append(['v', [0, thick]])  # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'v', 1):
                line_path.append(l)
            line_path.append(['h', [self.boxD/self.Dtabs/4 - self.pf/2, 0]])
        line_path.append(['h', [self.thick, 0]])
        #
        for i in range(self.Htabs):
            line_path.append(['v', [0, self.boxH/self.Htabs/4 + self.pf/2]])
            #line_path.append(['h', [-thick, 0]]) # replaced with  dimpled version
            for l in self.thickness_line(self.dimple, 'h', -1):
                line_path.append(l)
            line_path.append(['v', [0, self.boxH/self.Htabs/2 - self.pf]])
            line_path.append(['h', [self.thick, 0]])
            line_path.append(['v', [0, self.boxH/self.Htabs/4 + self.pf/2]])
        line_path.append(['h', [-self.thick, 0]])
        #
        for i in range(self.Dtabs):
            line_path.append(['h', [-self.boxD/self.Dtabs/4 + self.pf/2, 0]])
            #line_path.append(['v', [0, thick]])  # replaced with dimpled version
            for l in self.thickness_line(self.dimple, 'v', 1):  # this is the weird +1 instead of -1 dimple
                line_path.append(l)
            line_path.append(['h', [-self.boxD/self.Dtabs/2 - self.pf, 0]])
            line_path.append(['v', [0, -self.thick]])
            line_path.append(['h', [-self.boxD/self.Dtabs/4 + self.pf/2, 0]])
        line_path.append(['h', [-self.thick, 0]])
        #
        if self.kerf > 0.0:  # if fit perfectly - don't draw double line
            for i in range(self.Htabs):
                line_path.append(['v', [0, -self.boxH/self.Htabs/4 - self.pf/2]])
                line_path.append(['h', [self.thick, 0]])
                line_path.append(['v', [0, -self.boxH/self.Htabs/2 + self.pf]])
                #line_path.append(['h', [-thick, 0]])  # replaced with dimpled version
                for l in self.thickness_line(self.dimple, 'h', -1):
                    line_path.append(l)
                line_path.append(['v', [0, -self.boxH/self.Htabs/4 - self.pf/2]])
        return line_path

    ###
    def thin(self, sel):
        """ Parse the svg path - but don't use simplepath.parsePath because
             it converts all to M, L and no locals
            Instead - parse it ourselves                                      """
        svgtokens = ['M','L','H','V','C','S','Q','T','A','Z']
        for node in sel.iterchildren():
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                for t in svgtokens:
                    d = d.replace(t, ",%s"%t)
                    d = d.replace(t.lower(), ",%s"%t.lower())
                path = d.split(",")
                # remove empty cells
                if path.count("") > 0: path.remove("")
                #sys.stderr.write("thin Path length=%d\n"% len(path))
                # parse it ourselves
                prevx = path[0][-2]
                prevy = path[0][-1]
                prevtype = path[0][0]
                count = 1
                result = [path[0]]
                while count < len(path)-1:
                    line = path[count]
                    thistype = line[0]
                    thisx = line[1:].split()[0]
                    thisy = line[1:].split()[1]
                    if thistype == prevtype and thistype.lower() in ['h','v']:
                        # simplify
                        result.pop()  # remove last one
                        result.append("%s%f %f" % (prevtype, float(thisx) + float(prevx), float(thisy)+float(prevy)))
                    else:
                        result.append(line)
                    count += 1
                    prevx = thisx
                    prevy = thisy
                    prevtype = thistype
                # add last element (unsimplified)
                result.append(path[-1])
                # now inject back into d
                newd = ""
                for j in result:
                    newd += j
                #sys.stderr.write("new  length=%d\n" % len(result))
                node.set('d',newd)

            
    def trim_svg_path(self, sel):
        """ Force the svg we just made into its minimal config
            to try to get rid of extra nodes                    """
        # h and v become single numbers
        svgtokens = ['M','L','H','V','C','S','Q','T','A','Z']
        for node in sel.iterchildren():
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                for t in svgtokens:
                    d = d.replace(t, ",%s"%t)
                    d = d.replace(t.lower(), ",%s"%t.lower())
                path = d.split(",")
                # remove empty cells
                if path.count("") > 0: path.remove("")
                #
                count = 1
                result = [path[0]]
                while count < len(path):
                    line = path[count]
                    thistype = line[0]
                    thisx = line[1:].split()[0]
                    thisy = line[1:].split()[1]
                    if thistype.lower() =='h':
                        # simplify
                        result.append("%s%s" % (thistype, thisx))
                    elif thistype.lower() =='v':
                        # simplify
                        result.append("%s%s" % (thistype, thisy))
                    else:
                        result.append(line)
                    count += 1
                #result.append(path[-1])
                # now inject back into d
                newd = ""
                for j in result:
                    newd += j
                node.set('d',newd)




    ###--------------------------------------------
    ### The    main function    called    by    the    inkscape    UI
    def effect(self):
        # document dimensions (for centering)
        docW = self.unittouu(self.document.getroot().get('width'))
        docH = self.unittouu(self.document.getroot().get('height'))
        # extract fields from UI
        self.boxW  = self.unittouu(str(self.options.width) + self.options.units)
        self.boxH  = self.unittouu(str(self.options.height) + self.options.units)
        self.boxD  = self.unittouu(str(self.options.depth) + self.options.units)
        self.thick = self.unittouu(str(self.options.thickness) + self.options.units)
        self.kerf  = self.unittouu(str(self.options.kerf_size) + self.options.units)
        if self.kerf < 0.01: self.kerf = 0.0  # snap to 0 for UI error when setting spinner to 0.0
        self.Wtabs  = self.options.ntab_W
        self.Htabs  = self.options.ntab_H
        self.Dtabs  = self.options.ntab_D
        self.dimple = self.options.dimples
        line_width  = self.options.linewidth
        corners  = self.options.corners
        self.dimple_tri = self.options.dstyle
        self.annotation = self.options.annotation

        # Correct for thickness in dimensions
        if self.options.int_ext: # external so add thickness
            self.boxW -= self.thick*2
            self.boxH -= self.thick*2
            self.boxD -= self.thick*2
        # adjust for laser kerf (precise measurement)
        self.boxW += self.kerf
        self.boxH += self.kerf
        self.boxD += self.kerf

        # Precise fit or dimples (if kerf > 0.0)
        if self.dimple == False: # and kerf > 0.0:
            self.pf = self.kerf
        else:
            self.pf = 0.0
            
        # set the stroke width and line style
        sw = self.kerf
        if self.kerf == 0.0: sw = self.stroke_width
        ls = self.line_style
        if line_width: # user wants drawn line width to be same as kerf size
            ls['stroke-width'] = sw
        line_style = simplestyle.formatStyle(ls)

        ###--------------------------- 
        ### create the inkscape object
        box_id = self.uniqueId('box')
        self.box = g = inkex.etree.SubElement(self.current_layer, 'g', {'id':box_id})

        #Set local position for drawing (will transform to center of doc at end)
        lower_pos = 0
        left_pos  = 0
        # Draw Lid (using SVG path definitions)
        line_path = self.draw_WH_lid(left_pos, lower_pos)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-lid', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # draw the side of the box directly below
        if self.kerf > 0.0:
            lower_pos += self.boxH + (3*self.thick)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            lower_pos += self.boxH + self.thick  # at lower edge of lid
        left_pos += 0
        # Draw side of the box (placed below the lid)
        line_path = self.draw_WD_side(left_pos, lower_pos, corners=corners)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-longside1', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # draw the bottom of the box directly below
        if self.kerf > 0.0:
            lower_pos += self.boxD + (3*self.thick)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            lower_pos += self.boxD + self.thick # at lower edge
        left_pos += 0
        # Draw base of the box
        line_path = self.draw_WH_lid(left_pos, lower_pos, True)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-base', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # draw the second side of the box directly below
        if self.kerf > 0.0:
            lower_pos += self.boxH + (3*self.thick)
        else:  # kerf = 0 so don't draw extra lines and fit perfectly
            lower_pos += self.boxH + self.thick  # at lower edge of lid
        left_pos += 0
        # Draw side of the box (placed below the lid)
        line_path = self.draw_WD_side(left_pos, lower_pos, corners=corners)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-longside2', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # draw next on RHS of lid
        if self.kerf > 0.0:
            left_pos += self.boxW + (2*self.thick) # adequate space (could be a param for separation when kerf > 0)
        else:
            left_pos += self.boxW  # right at right edge of lid
        lower_pos = 0
        # Side of the box (placed next to the lid)
        line_path = self.draw_HD_side(left_pos, lower_pos, corners)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-endface2', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        # draw next on RHS of base
        if self.kerf > 0.0:
            lower_pos += self.boxH + self.boxD + 6*self.thick
        else:
            lower_pos += self.boxH +self.boxD + 2*self.thick
        # Side of the box (placed next to the lid)
        line_path = self.draw_HD_side(left_pos, lower_pos, corners, True)
        # Add to scene
        line_atts = { 'style':line_style, 'id':box_id+'-endface1', 'd':formatPath(line_path) }
        inkex.etree.SubElement(g, inkex.addNS('path','svg'), line_atts)

        
        ###----------------------------------------
        # Transform entire drawing to center of doc
        lower_pos += self.boxH*2 + self.boxD*2 + 2*self.thick
        left_pos += self.boxH + 2*self.thick
        g.set( 'transform', 'translate(%f,%f)' % ( (docW-left_pos)/2, (docH-lower_pos)/2))

        # The implementation algorithm has added intermediate short lines and doubled up when using h,v with extra zeros
        self.thin(g)  # remove short straight lines
        self.trim_svg_path(g)  # remove extra zero points

###
if __name__ == '__main__':
    e = LasercutBox()
    e.affect()
