#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import threading
import queue

class ImageCropperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 일괄 자르기 도구")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # 현재 이미지와 관련 변수
        self.current_image = None
        self.current_image_path = None
        self.tk_image = None
        self.preview_image = None
        self.image_paths = []
        self.crop_box = (100, 100, 500, 500)  # 기본 자르기 영역 (left, top, right, bottom)
        
        # 상태 변수
        self.is_processing = False
        self.progress_queue = queue.Queue()
        
        # 전체 레이아웃
        self.create_ui()
        
        # 프로그레스 업데이트 타이머
        self.root.after(100, self.check_progress_queue)
    
    def create_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 좌측 패널 (이미지 보기 및 자르기 영역 설정)
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 이미지 캔버스
        self.canvas_frame = ttk.LabelFrame(left_panel, text="미리보기")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="lightgray")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 자르기 영역 설정
        crop_frame = ttk.LabelFrame(left_panel, text="자르기 영역 설정")
        crop_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 자르기 영역 입력
        coords_frame = ttk.Frame(crop_frame)
        coords_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 왼쪽
        ttk.Label(coords_frame, text="왼쪽:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.left_var = tk.StringVar(value="100")
        ttk.Entry(coords_frame, textvariable=self.left_var, width=6).grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # 위쪽
        ttk.Label(coords_frame, text="위쪽:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.top_var = tk.StringVar(value="100")
        ttk.Entry(coords_frame, textvariable=self.top_var, width=6).grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        # 오른쪽
        ttk.Label(coords_frame, text="오른쪽:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.right_var = tk.StringVar(value="500")
        ttk.Entry(coords_frame, textvariable=self.right_var, width=6).grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # 아래쪽
        ttk.Label(coords_frame, text="아래쪽:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.bottom_var = tk.StringVar(value="500")
        ttk.Entry(coords_frame, textvariable=self.bottom_var, width=6).grid(row=1, column=3, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # 적용 버튼
        ttk.Button(coords_frame, text="미리보기 적용", command=self.update_preview).grid(row=0, column=4, rowspan=2, padx=(10, 0), pady=5)
        
        # 우측 패널 (폴더 선택 및 처리)
        right_panel = ttk.Frame(main_frame, width=250)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(0)  # 고정 너비 유지를 위한 설정
        
        # 입력 폴더 선택
        input_frame = ttk.LabelFrame(right_panel, text="입력 폴더")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_var, state="readonly").pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Button(input_frame, text="폴더 선택", command=self.select_input_folder).pack(padx=10, pady=(0, 10))
        
        # 파일 목록
        files_frame = ttk.LabelFrame(right_panel, text="이미지 파일 목록")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 스크롤바와 리스트박스
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(files_frame)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 파일 선택 이벤트 바인딩
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_select)
        
        # 출력 폴더 선택
        output_frame = ttk.LabelFrame(right_panel, text="출력 폴더")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, state="readonly").pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Button(output_frame, text="폴더 선택", command=self.select_output_folder).pack(padx=10, pady=(0, 10))
        
        # 처리 진행 상태
        progress_frame = ttk.LabelFrame(right_panel, text="진행 상태")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(padx=10, pady=(0, 10))
        
        # 실행 버튼
        self.process_button = ttk.Button(right_panel, text="이미지 자르기 시작", command=self.start_processing)
        self.process_button.pack(fill=tk.X, padx=10, pady=10)
    
    def select_input_folder(self):
        folder_path = filedialog.askdirectory(title="이미지가 있는 폴더 선택")
        if folder_path:
            self.input_var.set(folder_path)
            self.load_image_list(folder_path)
    
    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="잘린 이미지를 저장할 폴더 선택")
        if folder_path:
            self.output_var.set(folder_path)
    
    def load_image_list(self, folder_path):
        # 이미지 파일 목록 로드
        self.image_paths = []
        self.file_listbox.delete(0, tk.END)
        
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        try:
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(valid_extensions):
                    self.image_paths.append(os.path.join(folder_path, filename))
                    self.file_listbox.insert(tk.END, filename)
            
            # 첫 번째 이미지 선택
            if self.image_paths:
                self.file_listbox.selection_set(0)
                self.on_file_select(None)
            
            self.status_var.set(f"{len(self.image_paths)}개 이미지 로드됨")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 중 오류 발생: {e}")
    
    def on_file_select(self, event):
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            if 0 <= index < len(self.image_paths):
                self.load_image(self.image_paths[index])
    
    def load_image(self, image_path):
        try:
            self.current_image_path = image_path
            self.current_image = Image.open(image_path)
            self.update_preview()
            
            # 상태 업데이트
            filename = os.path.basename(image_path)
            self.status_var.set(f"이미지 로드됨: {filename}")
        except Exception as e:
            messagebox.showerror("오류", f"이미지 로드 중 오류 발생: {e}")
    
    def update_preview(self):
        if self.current_image is None:
            return
        
        try:
            # 자르기 영역 업데이트
            left = int(self.left_var.get())
            top = int(self.top_var.get())
            right = int(self.right_var.get())
            bottom = int(self.bottom_var.get())
            
            self.crop_box = (left, top, right, bottom)
            
            # 원본 이미지 복사본
            img_copy = self.current_image.copy()
            
            # 자르기 영역 표시
            self.preview_image = img_copy.crop(self.crop_box)
            
            # 캔버스 크기에 맞게 이미지 리사이즈
            self.display_image(img_copy)
        except ValueError:
            messagebox.showerror("오류", "자르기 좌표는 숫자여야 합니다.")
        except Exception as e:
            messagebox.showerror("오류", f"미리보기 업데이트 중 오류 발생: {e}")
    
    def display_image(self, img):
        # 캔버스 크기 가져오기
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # 캔버스가 너무 작으면 기본값 설정
        if canvas_width < 10:
            canvas_width = 400
        if canvas_height < 10:
            canvas_height = 300
        
        # 이미지 크기 계산
        img_width, img_height = img.size
        
        # 이미지 비율 유지하며 리사이즈
        ratio = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # 자르기 영역 표시
        draw_img = resized_img.copy()
        from PIL import ImageDraw
        
        draw = ImageDraw.Draw(draw_img)
        
        # 자르기 영역 좌표 계산
        crop_left = int(self.crop_box[0] * ratio)
        crop_top = int(self.crop_box[1] * ratio)
        crop_right = int(self.crop_box[2] * ratio)
        crop_bottom = int(self.crop_box[3] * ratio)
        
        # 자르기 영역 빨간색 사각형으로 표시
        draw.rectangle([crop_left, crop_top, crop_right, crop_bottom], outline="red", width=2)
        
        # 이미지 표시
        self.tk_image = ImageTk.PhotoImage(draw_img)
        self.canvas.config(width=new_width, height=new_height)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
    
    def start_processing(self):
        # 입력/출력 폴더 검증
        input_folder = self.input_var.get()
        output_folder = self.output_var.get()
        
        if not input_folder:
            messagebox.showerror("오류", "입력 폴더를 선택하세요.")
            return
        
        if not output_folder:
            messagebox.showerror("오류", "출력 폴더를 선택하세요.")
            return
        
        if not self.image_paths:
            messagebox.showerror("오류", "처리할 이미지가 없습니다.")
            return
        
        # 자르기 좌표 검증
        try:
            left = int(self.left_var.get())
            top = int(self.top_var.get())
            right = int(self.right_var.get())
            bottom = int(self.bottom_var.get())
            
            if left >= right or top >= bottom:
                messagebox.showerror("오류", "자르기 좌표가 올바르지 않습니다.")
                return
            
            self.crop_box = (left, top, right, bottom)
        except ValueError:
            messagebox.showerror("오류", "자르기 좌표는 숫자여야 합니다.")
            return
        
        # 출력 폴더 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # 처리 시작
        self.is_processing = True
        self.progress_var.set(0)
        self.status_var.set("처리 중...")
        self.process_button.config(state=tk.DISABLED)
        
        # 작업 스레드 시작
        thread = threading.Thread(target=self.process_images, args=(self.image_paths, output_folder, self.crop_box))
        thread.daemon = True
        thread.start()
    
    def process_images(self, image_paths, output_folder, crop_box):
        total_images = len(image_paths)
        processed = 0
        
        for img_path in image_paths:
            if not self.is_processing:
                break
            
            try:
                filename = os.path.basename(img_path)
                output_path = os.path.join(output_folder, filename)
                
                with Image.open(img_path) as img:
                    cropped_img = img.crop(crop_box)
                    cropped_img.save(output_path)
                
                processed += 1
                progress = (processed / total_images) * 100
                
                # 큐에 진행 상태 업데이트
                self.progress_queue.put(("progress", progress))
                self.progress_queue.put(("status", f"처리 중: {processed}/{total_images} - {filename}"))
            except Exception as e:
                self.progress_queue.put(("error", f"이미지 처리 오류 ({filename}): {e}"))
        
        # 작업 완료
        self.progress_queue.put(("completed", f"완료! {processed}/{total_images} 이미지 처리됨"))
    
    def check_progress_queue(self):
        try:
            while True:
                message_type, message = self.progress_queue.get_nowait()
                
                if message_type == "progress":
                    self.progress_var.set(message)
                elif message_type == "status":
                    self.status_var.set(message)
                elif message_type == "error":
                    messagebox.showerror("처리 오류", message)
                elif message_type == "completed":
                    self.status_var.set(message)
                    self.process_button.config(state=tk.NORMAL)
                    self.is_processing = False
                    messagebox.showinfo("완료", message)
        except queue.Empty:
            pass
        
        # 타이머 갱신
        self.root.after(100, self.check_progress_queue)

# 메인 함수
def main():
    root = tk.Tk()
    app = ImageCropperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
