#  -*- coding: utf-8 -*- 
import os
import os.path
import arcpy
from arcpy.sa import*
import time
import datetime
# 代码用于批处理计算landsat5影像的ndvi，将1、2、3、4、6波段合成，并利用6波段、ndvi反演地温
# 修改path内容更换文件夹路径
# written by ZWB

start = time.clock()

rootdir = 'F:/landsat5'

arcpy.CheckOutExtension("spatial")
arcpy.env.workspace = rootdir

list = os.listdir(rootdir)
# print list

for i in range(0, len(list)):
    path1 = os.path.join(rootdir, list[i])
    path = path1.replace("\\", "/")
    # print path
    path_result = path +'/result'
    # print path_result
    os.mkdir(path_result)
    # name = path[12:]
    name = os.path.basename(path)
    # print name
    # ——————————————————计算ndvi-----------------------------------------------
    # 获取红、近红波段
    # RED = name + '_B4.TIF'
    # NIR = name + '_B5.TIF'
    path2 = path + '/' + name
    RED = path2 + '_B4.TIF'
    NIR = path2 + '_B5.TIF'
    # # print RED
    # RED = Raster(path2 + '_B4.tif')
    # 计算ndvi
    num = arcpy.sa.Float(Raster(NIR) - Raster(RED))
    denom = arcpy.sa.Float(Raster(NIR) + Raster(RED))
    NIR_eq = arcpy.sa.Divide(num, denom)
    # 设置输出名称及路径
    result_ndvi_name = name + '_ndvi.tif'
    output_ndvi = path_result + '/' + result_ndvi_name
    # output_ndvi1 = path + '/' + result_ndvi_name
    # 输出ndvi计算结果
    NIR_eq.save(output_ndvi)
    # NIR_eq.save(output_ndvi1)
    print name, 'ndvi finished'

    # ——————————————————波段合成-----------------------------------------------
    # 获取合成波段，将所需波段放入列表
    B1 = path2 + '_B1.TIF'
    B2 = path2 + '_B2.TIF'
    B3 = path2 + '_B3.TIF'
    # B4 = name + '_B4.TIF'
    # B5 = name + '_B5.TIF'
    B6 = path2 + '_B6.TIF'
    raster = [B1, B2, B3, RED, B6]
    # print raster
    # 设置合成影像名称
    result_name = name + '_12346.tif'
    # 设置合成影像输出路径
    output = path_result + '/' + result_name
    # arcpy.CompositeBands_management(raster, "2.tif")
    # 利用gis波段合成函数，输出合成影像
    arcpy.CompositeBands_management(raster, output)
    print name, 'bands composite finished'

    # ——————————————————反演地表温度-----------------------------------------------
    # B10 = path2 + '_B10.TIF'
    band6 = Raster(B6)
    path3 = path_result + '/' + name + '_ndvi.tif'
    # print path3
    ndvi = Raster(path3)

    # 计算辐射值
    fsl = 0.055375 * band6 + 1.18243
    # 计算亮温
    K1 = 607.76
    K2 = 1260.56
    IRS = K2 / Ln(1 + K1 / fsl)
    # 计算比辐射率
    inTrueRaster1 = Square((ndvi - 0.05) / (0.7 - 0.05))
    pv = Con(ndvi < 0.05, 0, Con((ndvi >= 0.7), 1, Con(((ndvi >= 0.05) & (ndvi < 0.7)), inTrueRaster1)))
    Rv = 0.9332 + 0.0585 * pv
    Rx = 0.9902 + 0.1068 * pv
    inTrueRaster2 = 0.003796 * pv
    inTrueRaster3 = 0.003796 * (1 - pv)
    de = Con(pv < 0.5, inTrueRaster2, Con((pv >= 0.5), inTrueRaster3))
    ew10 = 0.995
    ev10 = 0.986
    es10 = 0.97215
    em10 = 0.97
    emiss10 = ev10 * pv * Rv + (1 - pv) * es10 * Rx + de
    # 中纬度冬季
    T0 = 10
    Ta = 19.2704 + 0.91118 * (273.15 + T0)
    w = 2.0
    r = 1.05371 - 0.14142 * w
    # 单窗算法估算地表温度
    a = -67.355351
    b = 0.458606
    C = emiss10 * r
    D = (1 - r) * (1 + (1 - emiss10) * r)
    LST = (a * (1 - C - D) + (b * (1 - C - D) + C + D) * IRS - D * Ta) / C - 273.15
    LST1 = Con(LST >= -10, LST, Con((LST > -50) & (LST < -10), -10))
    # 输出反演结果
    result_LST_name = name + '_LST.tif'
    output_LST = path_result + '/' + result_LST_name
    LST1.save(output_LST)
    print name, 'LST finished'

    # 计算运行时间
elapsed = (time.clock() - start)
print 'Time used:', elapsed, 's'