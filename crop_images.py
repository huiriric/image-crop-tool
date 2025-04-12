#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
from PIL import Image

def crop_images(input_dir, output_dir, crop_box, file_extensions=None):
    """
    지정된 디렉토리의 모든 이미지를 동일한 위치와 크기로 자릅니다.
    
    Args:
        input_dir (str): 입력 이미지가 있는 디렉토리 경로
        output_dir (str): 잘린 이미지를 저장할 디렉토리 경로
        crop_box (tuple): 자르기 좌표 (left, top, right, bottom)
        file_extensions (list): 처리할 파일 확장자 목록 (기본값: ['.jpg', '.jpeg', '.png'])
    """
    if file_extensions is None:
        file_extensions = ['.jpg', '.jpeg', '.png']
    
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 처리된 이미지 수
    processed_count = 0
    
    # 입력 디렉토리의 모든 파일 처리
    for filename in os.listdir(input_dir):
        # 파일 확장자 확인
        ext = os.path.splitext(filename)[1].lower()
        if ext not in file_extensions:
            continue
        
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            # 이미지 열기
            with Image.open(input_path) as img:
                # 이미지 자르기
                cropped_img = img.crop(crop_box)
                # 잘린 이미지 저장
                cropped_img.save(output_path)
                processed_count += 1
                print(f"처리 완료: {filename}")
        except Exception as e:
            print(f"오류 발생 (이미지: {filename}): {e}")
    
    print(f"\n총 {processed_count}개 이미지 처리 완료")

def main():
    parser = argparse.ArgumentParser(description='여러 이미지를 동일한 위치와 크기로 자르는 도구')
    parser.add_argument('input_dir', help='입력 이미지가 있는 디렉토리 경로')
    parser.add_argument('output_dir', help='잘린 이미지를 저장할 디렉토리 경로')
    parser.add_argument('--left', type=int, required=True, help='자르기 영역 좌측 좌표')
    parser.add_argument('--top', type=int, required=True, help='자르기 영역 상단 좌표')
    parser.add_argument('--right', type=int, required=True, help='자르기 영역 우측 좌표')
    parser.add_argument('--bottom', type=int, required=True, help='자르기 영역 하단 좌표')
    parser.add_argument('--extensions', nargs='+', default=['.jpg', '.jpeg', '.png'], 
                        help='처리할 파일 확장자 (기본값: .jpg .jpeg .png)')
    
    args = parser.parse_args()
    
    # 자르기 좌표
    crop_box = (args.left, args.top, args.right, args.bottom)
    
    # 이미지 자르기 실행
    crop_images(args.input_dir, args.output_dir, crop_box, args.extensions)

if __name__ == '__main__':
    main()
