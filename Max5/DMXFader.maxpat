{
	"patcher" : 	{
		"fileversion" : 1,
		"rect" : [ 1331.0, 245.0, 293.0, 423.0 ],
		"bglocked" : 0,
		"defrect" : [ 1331.0, 245.0, 293.0, 423.0 ],
		"openrect" : [ 0.0, 0.0, 0.0, 0.0 ],
		"openinpresentation" : 1,
		"default_fontsize" : 11.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 0,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 0,
		"toolbarvisible" : 1,
		"boxanimatetime" : 200,
		"imprint" : 0,
		"metadata" : [  ],
		"boxes" : [ 			{
				"box" : 				{
					"maxclass" : "inlet",
					"hint" : "led ctrl",
					"annotation" : "",
					"id" : "obj-10",
					"numoutlets" : 1,
					"numinlets" : 0,
					"outlettype" : [ "" ],
					"patching_rect" : [ 105.0, 15.0, 25.0, 25.0 ],
					"comment" : "led ctrl"
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "set $1",
					"id" : "obj-9",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 105.0, 180.0, 41.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "outlet",
					"hint" : "select next numberbox (bang)",
					"annotation" : "",
					"id" : "obj-8",
					"numoutlets" : 0,
					"numinlets" : 1,
					"patching_rect" : [ 60.0, 360.0, 25.0, 25.0 ],
					"comment" : "select next numberbox (bang)"
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "newobj",
					"text" : "t i 0",
					"id" : "obj-7",
					"numoutlets" : 2,
					"fontname" : "Arial",
					"numinlets" : 1,
					"outlettype" : [ "int", "int" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 15.0, 300.0, 32.5, 19.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "newobj",
					"text" : "int",
					"id" : "obj-6",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "int" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 15.0, 330.0, 32.5, 19.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "outlet",
					"hint" : "value",
					"annotation" : "",
					"id" : "obj-3",
					"numoutlets" : 0,
					"numinlets" : 1,
					"patching_rect" : [ 15.0, 360.0, 25.0, 25.0 ],
					"comment" : "value"
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "inlet",
					"hint" : "select number-box",
					"annotation" : "",
					"id" : "obj-2",
					"numoutlets" : 1,
					"numinlets" : 0,
					"outlettype" : [ "" ],
					"patching_rect" : [ 60.0, 15.0, 25.0, 25.0 ],
					"comment" : "select number-box"
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "inlet",
					"hint" : "set value",
					"annotation" : "",
					"id" : "obj-1",
					"numoutlets" : 1,
					"numinlets" : 0,
					"outlettype" : [ "" ],
					"patching_rect" : [ 15.0, 15.0, 25.0, 25.0 ],
					"comment" : "set value"
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "255",
					"id" : "obj-146",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 75.0, 330.0, 36.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "newobj",
					"text" : "sel 0 1",
					"id" : "obj-144",
					"numoutlets" : 3,
					"fontname" : "Arial",
					"numinlets" : 1,
					"outlettype" : [ "bang", "bang", "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 60.0, 300.0, 48.0, 19.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "newobj",
					"text" : "/ 255.",
					"id" : "obj-139",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "float" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 90.0, 105.0, 39.0, 19.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "color $1 $1 0.",
					"id" : "obj-140",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 90.0, 135.0, 78.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "led",
					"id" : "obj-141",
					"numoutlets" : 1,
					"offcolor" : [ 0.0, 0.0, 0.0, 1.0 ],
					"numinlets" : 1,
					"outlettype" : [ "int" ],
					"presentation_rect" : [ 15.0, 193.0, 35.0, 35.0 ],
					"patching_rect" : [ 45.0, 210.0, 20.0, 20.0 ],
					"presentation" : 1
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "select",
					"id" : "obj-14",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 60.0, 60.0, 40.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "set $1",
					"id" : "obj-84",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 15.0, 60.0, 41.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "message",
					"text" : "set $1",
					"id" : "obj-44",
					"numoutlets" : 1,
					"fontname" : "Arial",
					"numinlets" : 2,
					"outlettype" : [ "" ],
					"fontsize" : 11.0,
					"patching_rect" : [ 30.0, 270.0, 41.0, 17.0 ]
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "number",
					"id" : "obj-45",
					"numoutlets" : 2,
					"minimum" : 0,
					"fontname" : "Arial",
					"numinlets" : 1,
					"maximum" : 255,
					"outlettype" : [ "int", "bang" ],
					"presentation_rect" : [ 15.0, 172.0, 35.0, 19.0 ],
					"fontsize" : 11.0,
					"patching_rect" : [ 15.0, 240.0, 40.0, 19.0 ],
					"presentation" : 1
				}

			}
, 			{
				"box" : 				{
					"maxclass" : "slider",
					"id" : "obj-48",
					"numoutlets" : 1,
					"numinlets" : 1,
					"outlettype" : [ "" ],
					"presentation_rect" : [ 17.0, 14.0, 30.0, 156.0 ],
					"size" : 256.0,
					"patching_rect" : [ 15.0, 90.0, 27.0, 140.0 ],
					"presentation" : 1
				}

			}
 ],
		"lines" : [ 			{
				"patchline" : 				{
					"source" : [ "obj-45", 1 ],
					"destination" : [ "obj-8", 0 ],
					"hidden" : 0,
					"midpoints" : [ 45.5, 339.0, 69.5, 339.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-141", 0 ],
					"destination" : [ "obj-144", 0 ],
					"hidden" : 0,
					"midpoints" : [ 54.5, 233.0, 69.5, 233.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-7", 1 ],
					"destination" : [ "obj-9", 0 ],
					"hidden" : 0,
					"midpoints" : [ 38.0, 322.0, 148.0, 322.0, 148.0, 172.0, 114.5, 172.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-9", 0 ],
					"destination" : [ "obj-141", 0 ],
					"hidden" : 0,
					"midpoints" : [ 114.5, 203.0, 54.5, 203.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-144", 0 ],
					"destination" : [ "obj-6", 0 ],
					"hidden" : 0,
					"midpoints" : [ 69.5, 326.0, 24.5, 326.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-146", 0 ],
					"destination" : [ "obj-3", 0 ],
					"hidden" : 0,
					"midpoints" : [ 84.5, 355.0, 24.5, 355.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-6", 0 ],
					"destination" : [ "obj-3", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-7", 0 ],
					"destination" : [ "obj-6", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-45", 0 ],
					"destination" : [ "obj-7", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-14", 0 ],
					"destination" : [ "obj-45", 0 ],
					"hidden" : 0,
					"midpoints" : [ 69.5, 236.0, 24.5, 236.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-2", 0 ],
					"destination" : [ "obj-14", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-1", 0 ],
					"destination" : [ "obj-139", 0 ],
					"hidden" : 0,
					"midpoints" : [ 24.5, 47.0, 99.5, 47.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-45", 0 ],
					"destination" : [ "obj-139", 0 ],
					"hidden" : 0,
					"midpoints" : [ 24.5, 267.0, 75.0, 267.0, 75.0, 88.0, 99.5, 88.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-84", 0 ],
					"destination" : [ "obj-45", 0 ],
					"hidden" : 0,
					"midpoints" : [ 24.5, 81.0, 11.0, 81.0, 11.0, 234.0, 24.5, 234.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-45", 0 ],
					"destination" : [ "obj-44", 0 ],
					"hidden" : 0,
					"midpoints" : [ 24.5, 267.0, 39.5, 267.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-48", 0 ],
					"destination" : [ "obj-45", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-1", 0 ],
					"destination" : [ "obj-84", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-84", 0 ],
					"destination" : [ "obj-48", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-44", 0 ],
					"destination" : [ "obj-48", 0 ],
					"hidden" : 0,
					"midpoints" : [ 39.5, 295.0, 82.0, 295.0, 82.0, 83.0, 24.5, 83.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-139", 0 ],
					"destination" : [ "obj-140", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-140", 0 ],
					"destination" : [ "obj-141", 0 ],
					"hidden" : 0,
					"midpoints" : [ 99.5, 159.0, 54.5, 159.0 ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-144", 1 ],
					"destination" : [ "obj-146", 0 ],
					"hidden" : 0,
					"midpoints" : [  ]
				}

			}
, 			{
				"patchline" : 				{
					"source" : [ "obj-10", 0 ],
					"destination" : [ "obj-141", 0 ],
					"hidden" : 0,
					"midpoints" : [ 114.5, 165.0, 54.5, 165.0 ]
				}

			}
 ]
	}

}
