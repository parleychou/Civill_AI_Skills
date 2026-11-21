import os
import sys
import comtypes.client

comtypes.CoInitialize()
AttachToInstance = False # True to attach to a running instance of ETABS, False to start a new ETABS instance

#create API helper object
helper = comtypes.client.CreateObject('ETABSv1.Helper')
helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)

if AttachToInstance:
    try:
        myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject") 
    except (OSError, comtypes.COMError):
        print("No running instance of the program found or failed to attach.")
        sys.exit(-1)
else:
    myETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject") 
    myETABSObject.ApplicationStart()

#create SapModel object
SapModel = myETABSObject.SapModel

#initialize model
N_mm_C = 9     # N, mm, C
SapModel.InitializeNewModel(N_mm_C)

#create new blank model
ret = SapModel.File.NewBlank()

#define rectangular frame section property
ret = SapModel.PropFrame.SetRectangle('ColumConc', 'C30', 500, 500)
ret = SapModel.PropFrame.SetRectangle('BeamConc', 'C30', 500, 500)

#define frame section property modifiers
ModValue = [1000, 0, 0, 1, 1, 1, 1, 1]
ret = SapModel.PropFrame.SetModifiers('ColumConc', ModValue)
ret = SapModel.PropFrame.SetModifiers('BeamConc', ModValue)

#add frame object by coordinates
Coloumn_FrameName1 = ' '
Coloumn_FrameName2 = ' '
Coloumn_FrameName3 = ' '
Coloumn_FrameName4 = ' '
[Coloumn_FrameName1, ret] = SapModel.FrameObj.AddByCoord(0, 0, 0, 0, 0, 3000, Coloumn_FrameName1, 'ColumConc', '1', 'Global')
[Coloumn_FrameName2, ret] = SapModel.FrameObj.AddByCoord(6000, 0, 0, 6000, 0, 3000, Coloumn_FrameName2, 'ColumConc', '2', 'Global')
[Coloumn_FrameName3, ret] = SapModel.FrameObj.AddByCoord(0, 6000, 0, 0, 6000, 3000, Coloumn_FrameName3, 'ColumConc', '3', 'Global')
[Coloumn_FrameName4, ret] = SapModel.FrameObj.AddByCoord(6000, 6000, 0, 6000, 6000, 3000, Coloumn_FrameName4, 'ColumConc', '4', 'Global')

FrameNameList = [Coloumn_FrameName1, Coloumn_FrameName2, Coloumn_FrameName3, Coloumn_FrameName4]    

#assign point object restraint at base
for FrameName in FrameNameList:
    PointName1 = ' '
    PointName2 = ' '
    Restraint = [True, True, True, True, True, True] # 固接支座
    [PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(FrameName, PointName1, PointName2)
    ret = SapModel.PointObj.SetRestraint(PointName1, Restraint)

Beam_FrameName1 = ' '
Beam_FrameName2 = ' '
Beam_FrameName3 = ' '
Beam_FrameName4 = ' '
[Beam_FrameName1, ret] = SapModel.FrameObj.AddByCoord(0, 0, 3000, 6000, 0, 3000, Beam_FrameName1, 'BeamConc', '1', 'Global')
[Beam_FrameName2, ret] = SapModel.FrameObj.AddByCoord(6000, 0, 3000, 6000, 6000, 3000, Beam_FrameName2, 'BeamConc', '2', 'Global')
[Beam_FrameName3, ret] = SapModel.FrameObj.AddByCoord(6000, 6000, 3000, 0, 6000, 3000, Beam_FrameName3, 'BeamConc', '3', 'Global')
[Beam_FrameName4, ret] = SapModel.FrameObj.AddByCoord(0, 6000, 3000, 0, 0, 3000, Beam_FrameName4, 'BeamConc', '4', 'Global')
Beam_FrameNameList = [Beam_FrameName1, Beam_FrameName2, Beam_FrameName3, Beam_FrameName4]

#refresh view, update (initialize) zoom
ret = SapModel.View.RefreshView(0, False)

# #add load patterns
LTYPE_OTHER = 8
ret = SapModel.LoadPatterns.Add('1', LTYPE_OTHER, 1, True)
ret = SapModel.LoadPatterns.Add('2', LTYPE_OTHER, 0, True)

# assign loading for load pattern 1
[PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(Beam_FrameName1, PointName1, PointName2)
PointLoadValue = [0,0,-10,0,0,0]
ret = SapModel.PointObj.SetLoadForce(PointName1, '2', PointLoadValue)
ret = SapModel.FrameObj.SetLoadDistributed(Beam_FrameName1, '1', 1, 10, 0, 1, 1800, 1800)

#save model
ModelPath = r"C:\Users\d\Desktop\新建文件夹 (2)\test.edb"
ret = SapModel.File.Save(ModelPath)

#run model (this will create the analysis model)
ret = SapModel.Analyze.RunAnalysis()

#initialize for results
[PointName1, PointName2, ret] = SapModel.FrameObj.GetPoints(Beam_FrameName1, PointName1, PointName2)

#get results for load cases 1
NumberResults = 0
Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3 = [], [], [], [], [], [], [], [], [], [], []
ObjectElm = 0
ret = SapModel.Results.Setup.DeselectAllCasesAndCombosForOutput()
ret = SapModel.Results.Setup.SetCaseSelectedForOutput(str(1))
[NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3, ret] = SapModel.Results.JointDispl(PointName2, ObjectElm, NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3)

# close the program
ret = myETABSObject.ApplicationExit(False)
SapModel = None
mySapObject = None

