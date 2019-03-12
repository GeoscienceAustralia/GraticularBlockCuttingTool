# Dictionary: generic name as key, each tuple is a collection of truncated, short names and some variants
#
# some data sets use Number_of_Vertices, and some use Number_Of_Vertices
AltFieldName_dict = {
"OBJECTID":("OBJECTID","OID","FID"),
"BLOCK_ID":("BLOCK_ID","BlkID"),
"Map_Sheet":("Map_Sheet","MapSheet"),
"Block_Number":("Block_Number","Block_Numb","BlkNo"),
"Block_Letter":("Block_Letter","Block_Lett","BlkLetter"),
"Block_Number_XXX":("Block_Number_XXX","BlkNoXXX"),
"Block_ID_1D":("Block_ID_1D","Block_ID_1","BlkID_1D","BLK_ID_1D"),
"WMB_ID":("0WMB_ID",),
"Country":("Country",),
"Offshore_Area":("Offshore_Area","Offshore_A","Ofshr_Area"),
"Epoch":("Epoch",),
"Datum":("Datum",),
"Vertices":("Vertices",),
"Cut":("Cut",),
"Part":("Part",),
"Total":("Total",),
"Comment":("Comment",),
"Number_Of_Vertices":("Number_Of_Vertices","Number_of_Vertices","Number_of","Number_Of_","NoOfVertx"),
"Area_Acres":("Area_Acres","AreaAcres","Area_AC"),
"Area_Hectares":("Area_Hectares","Area_Hecta","AreaHectar","Area_HA"),
"Map_Name":("Map_Name",),
"LEGSOU":("LEGSOU",),
"Registry_No":("Registry_No","Registry_N","REG_No"),
"IP_Owner":("IP_Owner",),
"Licence":("Licence",),
"Disclaimer":("Disclaimer",)
}


# all_field_names = AltFieldName_dict["Suck"]
#
# for each_field_name in all_field_names:
#
#     print (each_field_name)