import os
import shutil

moves = {
    "AI_Engineering_Interview.epub": "Books/3_Career_and_Professional_Development/Interview_Prep/",
    "AI_Engineering_Interview.pdf": "Books/3_Career_and_Professional_Development/Interview_Prep/",
    "Acing_the_System_Design_Interview.epub": "Books/3_Career_and_Professional_Development/Interview_Prep/",
    "Acing_the_System_Design_Interview.pdf": "Books/3_Career_and_Professional_Development/Interview_Prep/",
    "Build_Your_First_Home_Server.pdf": "Books/1_Computer_Science_Fundamentals/Systems_and_OS/",
    "Designing_Data_Intensive_Applications_2nd_Edition.epub": "Books/2_Software_Engineering/Software_Architecture_and_Design/",
    "Designing_Data_Intensive_Applications_2nd_Edition.pdf": "Books/2_Software_Engineering/Software_Architecture_and_Design/",
    "Mastering_RESTful_Web_Services_with_Java.pdf": "Books/1_Computer_Science_Fundamentals/Programming_Languages/Java/",
    "Mastering_React_js_Interviews_For_MiddleSenior_Developers.pdf": "Books/3_Career_and_Professional_Development/Interview_Prep/",
    "OpenClaw_AI_in_Production.pdf": "Books/2_Software_Engineering/Artificial_Intelligence/",
    "The_Modern_Guide_to_AI_Powered_Web_Scraping_and_Automation.pdf": "Books/2_Software_Engineering/Artificial_Intelligence/",
    "Web_Scraping_With_Python.pdf": "Books/1_Computer_Science_Fundamentals/Programming_Languages/Python/"
}

for src, dest_dir in moves.items():
    src_path = os.path.join("Inbox", src)
    if os.path.exists(src_path):
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(src_path, os.path.join(dest_dir, src))
        print(f"Moved {src} to {dest_dir}")
