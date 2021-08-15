import json
import os,time
import base64
from PIL import Image
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ocr.v20181119 import ocr_client, models

# 获取腾讯API密钥：https://console.cloud.tencent.com/cam/capi
SecretId = ""
SecretKey = ""

def getPrintImgMode1(rootPath):
    # 获取所有图片绝对路径的list
    imgList = getImgPath(rootPath)
    # 判断图片目录下是否有output文件夹
    replacePath = os.path.dirname(imgList[0]).replace('\\','/')
    if not os.path.isdir(replacePath+"/output"):
        os.makedirs(replacePath+"/output")
    imgListLen = len(imgList)
    i = 0
    count = 1
    while(i<imgListLen):
        if ( i % 2 !=0 ):
            print('正在拼合身份证图像.....进度：当前处理{}，剩余{}，总共{}'.format(count, int((imgListLen/2)-count)),int((imgListLen/2)))
            # getPrintImg(身份证正面路径， 身份证背面路径)
            getPrintImg(imgList[i-1], imgList[i])
            count+= 1
        i+=1
    print('处理完成！请查看图片所在目录下output文件夹')

# 获取拼合的打印图像
def getPrintImg(imgPath1, imgPath2):
    # 清空tmp文件夹
    clearTmp()
    # 获取身份证正面图片base64
    imgBase64_img1 = picture2base(imgPath1)
    # 裁剪身份证正面
    cropIdCardFront(imgBase64_img1)
    time.sleep(1)
    # 获取身份证背面图片base64
    imgBase64_img2 = picture2base(imgPath2)
    # 裁剪身份证背面
    cropIdCardBack(imgBase64_img2)
    time.sleep(1)
    # 设置300DPI的A4白板
    width, height = int(8.27 * 300), int(11.7 * 300) # A4 at 300dpi
    page = Image.new('RGB', (width, height), 'white')
    # 将正反面贴到白板，box(x,y) x表示图片左上角在白板上横向位置，y表示纵向位置
    page.paste(Image.open('tmp/Front.jpg'), box=(710, 720))
    page.paste(Image.open('tmp/Back.jpg'), box=(710, 1740))
    # 获取身份证正反面图片原始名称用于分辨
    img1Name = imgPath1.split("\\")[-1].split(".")[0]
    img2Name = imgPath2.split("\\")[-1].split(".")[0]
    imgName = img1Name +'+'+ img2Name
    # 写入文件
    outputPath = os.path.dirname(imgPath1).replace('\\','/')
    page.save(outputPath+'/output/{}.jpg'.format(imgName))
    time.sleep(1)
    clearTmp()


# 图片转base64
def picture2base(path):
    img_file = open(path,'rb')
    img_b64encode = base64.b64encode(img_file.read())  # 使用base64进行加密
    ImgBase64 = img_b64encode.decode()
    return ImgBase64

# base64转图片        
def base2picture(ImgBase64Data, name):
    imgdata = base64.b64decode(ImgBase64Data)
    file = open('tmp/'+ name +'.jpg','wb')
    file.write(imgdata)
    file.close()

# 将图片转为身份证大小
def set_image_dpi_resize(imgpath, name):
    img_switch = Image.open(imgpath) # 读取图片
    image_resize = img_switch.resize((1063,710), Image.ANTIALIAS)
    image_resize = image_resize.convert('RGB')
    image_resize.save('tmp/resize_'+ name +'.jpg',dpi=(300, 300))
    img_switch.close() 
    image_resize.close()

# 获取指定目录下所有图片的绝对路径
def getImgPath(rootPath):
    # time.sleep(2)
    list = []
    for root, dirs, files in os.walk(rootPath):
        for name in files:
             if(name.lower().endswith(('.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff'))):
                list.append(os.path.join(root, name))
    print('获取指定目录下所有图片路径成功！')
    print('-------------------------------------')
    return list

# 清空tmp文件夹
def clearTmp():
    cur_path1='./tmp'
    ls=os.listdir(cur_path1)
    for i in ls:
        c_path=os.path.join(cur_path1,i)
        os.remove(c_path)

# 初始化tmp文件夹
def initTmp():
    # time.sleep(2)
    if os.path.isdir("./tmp"):
        cur_path1='./tmp'
        ls=os.listdir(cur_path1)
        for i in ls:
            c_path=os.path.join(cur_path1,i)
            os.remove(c_path)
    else:
        os.makedirs("tmp")
    os.close
    print("初始化成功！ ")

# 裁剪身份证正面
def cropIdCardFront(ImgBase64Data):
    try: 
        cred = credential.Credential(SecretId, SecretKey) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"
        
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ocr_client.OcrClient(cred, "ap-guangzhou", clientProfile) 

        req = models.IDCardOCRRequest()
        params = {
            "ImageBase64": ImgBase64Data,
            "Config": "{\"CropIdCard\":true,\"CropPortrait\":false}"
        }
        req.from_json_string(json.dumps(params))

        resp = client.IDCardOCR(req) 
        # print(resp.to_json_string()) 
        respJson = json.loads(resp.to_json_string())
        # print(respJson)
        respImgBase64 = json.loads(respJson["AdvancedInfo"])["IdCard"]
        # return respImgBase64
        base2picture(respImgBase64, 'Front')
        set_image_dpi_resize('tmp/Front.jpg','Front')
    except TencentCloudSDKException as err: 
        print(err)

# 裁剪身份证反面
def cropIdCardBack(ImgBase64Data):
    try: 
        cred = credential.Credential(SecretId, SecretKey) 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ocr.tencentcloudapi.com"
        
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ocr_client.OcrClient(cred, "ap-guangzhou", clientProfile) 

        req = models.IDCardOCRRequest()
        params = {
            "ImageBase64": ImgBase64Data,
            "CardSide": "BACK",
            "Config": "{\"CropIdCard\":true,\"CropPortrait\":false}"
        }
        req.from_json_string(json.dumps(params))

        resp = client.IDCardOCR(req) 
        # print(resp.to_json_string()) 
        respJson = json.loads(resp.to_json_string())
        # print(respJson)
        respImgBase64 = json.loads(respJson["AdvancedInfo"])["IdCard"]
        # return respImgBase64
        base2picture(respImgBase64, 'Back')
        set_image_dpi_resize('tmp/Back.jpg', 'Back')

    except TencentCloudSDKException as err: 
        print(err)
  

if __name__ == '__main__':
    print("使用说明：")
    print("0、输入 0 为手动拼合两张身份证正反面，需要分别指定路径")
    print("1、输入 1 为自动批量拼合两张身份证正反面")
    # mp.mod_print("2、输入 2 为上面身份证正面，下面银行卡", mp.ANSI_BLUE, mp.ANSI_BLACK_BACKGROUND, mp.MOD_HIGHLIGHT)
    # mp.mod_print("3、输入 3 为上面身份证正面，中间身份证反面，下面银行卡", mp.ANSI_CYAN, mp.ANSI_BLACK_BACKGROUND, mp.MOD_HIGHLIGHT)
    print("------------------------------------------------------")
    mode = input("请输入拼合模式： ")
    while(mode not in ['0', '1']):
        mode = input("模式输入错误，请重新输入拼合模式： ")
    print("当前模式为{}".format(mode))
    initTmp()
    print("------------------------------------------------------")
    rootPath = input('请输入图片路径： ')
    while (not os.path.isdir(rootPath)):
        print("路径输入错误，请重新输入路径")
        rootPath = input('请输入图片路径： ')
    # print(rootPath)
    if(mode == "0"):
        imgPathFront = input('请输入身份证正面图片完整路径： ')
        imgPathBack = input('请输入身份证反图片完整路径： ')
        getPrintImg(imgPathFront, imgPathBack)
    if (mode == "1"):
        getPrintImgMode1(rootPath)
    # elif (mode == "2"):
    #     getPrintImgMode2(rootPath)
    # elif (mode == "3"):
    #     getPrintImgMode3(rootPath)
    else:
        print("输入错误")
    input("按任意键退出程序..........")


    
    