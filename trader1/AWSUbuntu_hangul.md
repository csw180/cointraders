sudo apt install language-pack-ko        
sudo apt install language-pack-ko-base       
sudo apt install localepurge      # 설정 스크립트가 뜨면 euckr 선택      

/var/lib/locales/supported.d/ko        
ko_KR.EUC-KR EUC-KR   # 추가     
         
sudo locale-gen ko_KR.UTF-8       
sudo dpkg-reconfigure locales      
         
/etc/environment      
LANG="ko_KR.UTF-8"   # 추가        
LANG="ko_KR.EUC-KR"   # 추가      
         
cd~       
vi .bach_profile       
LANG="ko_KR.UTF-8"      
LANGUAGE="ko_KR:ko:en_US:en"      
               
                 
*** 언어팩 삭제할때            
sudo apt remove language-pack-ko             
sudo apt remove language-pack-ko-base        
               
                    
** 윈도우등에서 편집한 파일중 cp949로 엔코딩된 파일이 그대로 넘어온경우 파일의 엔코딩을 강제로 수정                   
sudo apt install convmv nautlius-filename-repairer              
convmv -r -f cp040 -t utf8 [파일 혹은 디렉토리명]              
