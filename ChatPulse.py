import tkinter as tk
import time
from tkinter import ttk
import vlc
from tkinter import filedialog, messagebox
from datetime import timedelta
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from yt_dlp import YoutubeDL
from os.path import expanduser
import pytchat
import numpy as np
import ffmpeg
import json

class MediaPlayerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Player")
        self.geometry("1350x800")
        self.configure(bg="#f0f0f0")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor="#e0e0e0",
            background="#2196F3",
            thickness=3
        )

        self.initialize_player()

    def initialize_player(self):
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.current_file = None
        self.playing_video = False
        self.video_paused = False
        self.cut_start_time = None
        self.cut_end_time = None
        self.output_directory = None

        self.create_widgets()

    def create_widgets(self):
        # メインフレーム
        self.main_frame = tk.Frame(self, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側のフレーム（動画用）
        self.left_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右側のフレーム（空白用）
        self.right_frame = tk.Frame(self.main_frame, bg="#f0f0f0", width=400)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas
        self.media_canvas = tk.Canvas(self.left_frame, bg="black")
        self.media_canvas.pack(fill=tk.BOTH, expand=True)

        self.file_frame = tk.Frame(self,bg="#f0f0f0")
        self.file_frame.pack(pady=5)

        # ウィンドウサイズ変更時のイベントバインド
        self.bind("<Configure>", self.on_window_resize)

        # 以下、既存のウィジェット作成コード
        self.select_file_button = tk.Button(
            self.file_frame,
            text="Select File",
            font=("Arial", 12, "bold"),
            command=self.select_file,
        )
        
        self.select_file_button.pack(side=tk.LEFT,pady=5)

        self.select_output_button = tk.Button(
            self.file_frame,
            text="保存先選択",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.select_output_directory,
        )
        self.select_output_button.pack(side=tk.LEFT, padx=5, pady=5)      

        self.time_label = tk.Label(
            self,
            text="00:00:00 / 00:00:00",
            font=("Arial", 12, "bold"),
            fg="#555555",
            bg="#f0f0f0",
        )
        self.time_label.pack(pady=5)

        # コントロールボタンフレーム
        self.control_buttons_frame = tk.Frame(self, bg="#f0f0f0")
        self.control_buttons_frame.pack(pady=5)

        self.play_button = tk.Button(
            self.control_buttons_frame,
            text="Play",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.play_video,
        )
        self.play_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.pause_button = tk.Button(
            self.control_buttons_frame,
            text="Pause",
            font=("Arial", 12, "bold"),
            bg="#FF9800",
            fg="white",
            command=self.pause_video,
        )
        self.pause_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.stop_button = tk.Button(
            self.control_buttons_frame,
            text="Stop",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=self.stop,
        )
        self.stop_button.pack(side=tk.LEFT, pady=5)

        self.fast_forward_button = tk.Button(
            self.control_buttons_frame,
            text="+10s",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.fast_forward,
        )
        self.fast_forward_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.rewind_button = tk.Button(
            self.control_buttons_frame,
            text="-10s",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.rewind,
        )
        self.rewind_button.pack(side=tk.LEFT, pady=5)

        self.start_cut_button = tk.Button(
            self.control_buttons_frame,
            text="切り取りはじめ",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.start_cut,
        )
        self.start_cut_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.stop_cut_button = tk.Button(
            self.control_buttons_frame,
            text="切り取りおわり",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.stop_cut,
        )
        self.stop_cut_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.merge_button = tk.Button(
            self.control_buttons_frame,
            text="動画を結合",
            font=("Arial", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self.merge_video,
        )
        self.merge_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 入力フォーム
        self.input_frame = tk.Frame(self, bg="#f0f0f0")
        self.input_frame.pack(pady=10)

        self.input_entry = tk.Entry(self.input_frame, width=20)
        self.input_entry.pack(side=tk.LEFT, padx=5)

        self.submit_button = tk.Button(self.input_frame, text="Submit", command=self.show_graph)
        self.submit_button.pack(side=tk.LEFT)

        # プログレスバーとグラフを含むフレーム
        self.progress_frame = tk.Frame(self, bg="#f0f0f0")
        self.progress_frame.pack(fill=tk.X, padx=10, pady=5)

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            style="Custom.Horizontal.TProgressbar",
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        self.progress_bar.pack(pady=50)

        self.progress_bar.bind("<Button-1>", self.on_progress_click)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.progress_frame)
        self.canvas.draw()
        self.graph_widget = self.canvas.get_tk_widget()
        self.graph_widget.pack_forget()
        self.figure.subplots_adjust(left=-1, right=1, bottom=0, top=1)

        self.graph_widget.place(in_=self.progress_frame, anchor="nw", relwidth=1, relheight=1)
        self.progress_frame.lower(self.graph_widget)

        self.graph_widget.bind("<Button-1>", self.on_graph_click)

        self.create_volume_slider()
    
        """
        ここらへん追加して
        """
        # 切り取り動画のウィジェット
        #新しいフレームを作成
        self.cut_info_frame = tk.Frame(self.right_frame, bg="#f0f0f0", relief="groove", borderwidth=2)
        self.cut_info_frame.pack(fill=tk.X, padx=5, pady=2)

        self.header_frame = tk.Frame(self.cut_info_frame, bg="#f0f0f0", height=30)
        self.header_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # 開始時間、終了時間、名前入力フォーム、削除ボタンを表示
        self.start_time_label = tk.Label(self.header_frame, text="開始時間", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.start_time_label.pack(side=tk.LEFT, padx=2, pady=2)
        self.start_time_label.pack_propagate(False)

        self.end_time_label = tk.Label(self.header_frame, text="終了時間", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.end_time_label.pack(side=tk.LEFT, padx=2, pady=2)
        self.end_time_label.pack_propagate(False)

        self.name_label = tk.Label(self.header_frame, text="名前", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.name_label.pack(side=tk.LEFT, padx=2, pady=2)
        self.name_label.pack_propagate(False)

        self.delete_label = tk.Label(self.header_frame, text="削除", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.delete_label.pack(side=tk.LEFT, padx=2, pady=2)
        self.delete_label.pack_propagate(False)



    def select_output_directory(self):
        self.output_directory = filedialog.askdirectory()
        if self.output_directory:
            messagebox.showinfo("保存先設定", f"保存先ディレクトリ: {self.output_directory}")

    def on_window_resize(self, event):
        # ウィンドウサイズに応じてCanvasのサイズを調整
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        canvas_width = int(window_width * 0.6)  # 画面の60%
        canvas_height = int(window_height * 0.6)  # 画面の60%
        self.media_canvas.config(width=canvas_width, height=canvas_height)

    # 以下、既存のメソッドは変更なし

    def on_progress_click(self, event):
        width = self.progress_bar.winfo_width()
        if width == 0:
            return
        fraction = event.x / width
        value = fraction * 100
        self.progress_bar["value"] = value
        self.set_video_position(value)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.mp4 *.avi")]
        )
        if file_path:
            self.current_file = file_path
            self.time_label.config(text="00:00:00 / " + self.get_duration_str())
            self.play_video()

    def get_duration_str(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
            return total_duration_str
        return "00:00:00"

    def play_video(self):
        if not self.current_file:
            messagebox.showerror("エラー", "ファイルが選択されてません。")
            return
        if not self.playing_video:
            media = self.instance.media_new(self.current_file)
            self.media_player.set_media(media)
            self.media_player.set_hwnd(self.media_canvas.winfo_id())
            self.media_player.play()
            self.playing_video = True

    def fast_forward(self):
        if self.playing_video:
            current_time = self.media_player.get_time() + 10000
            self.media_player.set_time(current_time)

    def rewind(self):
        if self.playing_video:
            current_time = self.media_player.get_time() - 10000
            self.media_player.set_time(current_time)

    def pause_video(self):
        if self.playing_video:
            if self.video_paused:
                self.media_player.play()
                self.video_paused = False
                self.pause_button.config(text="Pause")
            else:
                self.media_player.pause()
                self.video_paused = True
                self.pause_button.config(text="Resume")

    def stop(self):
        if self.playing_video:
            self.media_player.stop()
            self.playing_video = False
            self.time_label.config(text="00:00:00 / " + self.get_duration_str())

    def start_cut(self):
        if self.playing_video:
            self.cut_start_time = self.media_player.get_time() // 1000
            messagebox.showinfo("開始時間設定", f"切り取り開始時間: {self.format_time(self.cut_start_time)}")

    def stop_cut(self):
        if self.playing_video:
            self.cut_end_time = self.media_player.get_time() // 1000
            messagebox.showinfo("終了時間設定", f"切り取り終了時間: {self.format_time(self.cut_end_time)}")

        """
        ここらへんも
        """
        # 各ウィジェット用のサブフレームを作成
        cut_sub_info_frame = tk.Frame(self.cut_info_frame, bg="#f0f0f0")
        cut_sub_info_frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        time_frame = tk.Frame(cut_sub_info_frame, bg="#f0f0f0", relief="ridge", borderwidth=1)
        time_frame.pack(side=tk.LEFT, padx=2, pady=2)

        input_frame = tk.Frame(cut_sub_info_frame, bg="#f0f0f0", relief="ridge", borderwidth=1)
        input_frame.pack(side=tk.LEFT, padx=2, pady=2)

        button_frame = tk.Frame(cut_sub_info_frame, bg="#f0f0f0", relief="ridge", borderwidth=1)
        button_frame.pack(side=tk.LEFT, padx=2, pady=2)

        # 開始時間ラベル
        start_label = tk.Label(
            time_frame,
            text=self.format_time(self.cut_start_time),
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            relief="sunken",
            width=10
        )
        start_label.pack(side=tk.LEFT, padx=5)

        # 終了時間ラべル
        end_label = tk.Label(
            time_frame,
            text=self.format_time(self.cut_end_time),
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            relief="sunken",
            width=10
        )
        end_label.pack(side=tk.LEFT, padx=5)

        # 名前入力フォーム
        name_entry = tk.Entry(input_frame, width=20, relief="sunken")
        name_entry.pack(side=tk.LEFT, fill=tk.X, padx=5)

        def delete_frame_and_file():
            try:
                if os.path.exists(cut_filepath):
                    os.remove(cut_filepath)
                    cut_sub_info_frame.destroy()
                    messagebox.showinfo("削除完了", "切り取り情報とファイルを削除しました")
                else:
                    messagebox.showwarning("警告", "対応する動画ファイルが見つかりません")
                    cut_sub_info_frame.destroy()
            except Exception as e:
                    messagebox.showerror("エラー", f"削除中にエラーが発生しました: {e}")

        # 削除ボタン
        delete_button = tk.Button(
            button_frame,
            text="削除",
            font=("Arial", 12, "bold"),
            bg="#F44336",
            fg="white",
            command=delete_frame_and_file,
            relief="raised"
        )
        delete_button.pack(side=tk.LEFT, padx=5)

        cut_filepath = self.cut_video()

    def cut_video(self):
        if not self.current_file or self.cut_start_time is None or self.cut_end_time is None:
            messagebox.showerror("エラー", "切り取り時間を設定してください！")
            return

        # 保存先ディレクトリが未設定の場合、設定を促す
        if not self.output_directory:
            self.output_directory = filedialog.askdirectory(title="保存先ディレクトリを選択してください")
            if not self.output_directory:
                messagebox.showerror("エラー", "保存先が選択されていません。")
                return

        # 自動生成されるファイル名（例: 元ファイル名_cut_開始時刻_終了時刻.mp4）
        original_filename = os.path.basename(self.current_file)
        filename_without_ext = os.path.splitext(original_filename)[0]
        new_filename = f"{filename_without_ext}_cut_{self.cut_start_time}_{self.cut_end_time}.mp4"
        output_path = os.path.join(self.output_directory, new_filename)

        try:
            input_file = self.current_file
            start_time = self.cut_start_time
            duration = self.cut_end_time - self.cut_start_time
            ffmpeg.input(input_file, ss=start_time, t=duration).output(output_path, vcodec='libx264', crf=18, preset='slow', video_bitrate='10M', vf='scale=trunc(iw/2)*2:trunc(ih/2)*2').run()
            messagebox.showinfo("成功", f"切り取った動画を保存しました！\n保存先: {output_path}")
            return output_path
        except Exception as e:
            messagebox.showerror("エラー", f"切り取りに失敗しました: {e}")

    def format_time(self, seconds):
        return str(timedelta(seconds=seconds))

    def merge_video(self):
        pass

    def set_video_position(self, value):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            position = int((float(value) / 100) * total_duration)
            self.media_player.set_time(position)

    def update_video_progress(self):
        if self.playing_video:
            total_duration = self.media_player.get_length()
            if total_duration > 0:
                current_time = self.media_player.get_time()
                progress_percentage = (current_time / total_duration) * 100
                self.progress_bar["value"] = progress_percentage

                current_time_str = str(timedelta(milliseconds=current_time))[:-3]
                total_duration_str = str(timedelta(milliseconds=total_duration))[:-3]
                self.time_label.config(text=f"{current_time_str} / {total_duration_str}")

        self.after(1000, self.update_video_progress)

    def create_volume_slider(self):
        self.volume_slider = tk.Scale(
            self.control_buttons_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            length=150,
            command=self.change_volume,
            label="Volume",
            bg="#f0f0f0",
        )
        self.volume_slider.set(50)
        self.volume_slider.pack(side=tk.LEFT, padx=10)

    def change_volume(self, value):
        volume = int(value)
        self.media_player.audio_set_volume(volume)

    def show_graph(self):
        YT_url = self.input_entry.get()
        video_path = self.youtube_dl(YT_url)
        self.play_downloaded_video(video_path)
        self.create_graph(YT_url, 5)
        self.progress_frame.lower(self.graph_widget)

    def play_downloaded_video(self, video_path):
        """
        ダウンロードした動画を再生します。
        """
        self.current_file = video_path
        self.time_label.config(text="00:00:00 / " + self.get_duration_str())
        self.play_video()

    def youtube_dl(self, YT_url):
        """
        Youtube動画をダウンロードし、ファイルパスを返します。
        """
        ydl_video_opts = {
            'outtmpl': '%(id)s.%(ext)s',
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        }
        with YoutubeDL(ydl_video_opts) as ydl:
            info = ydl.extract_info(YT_url, download=True)
            filename = ydl.prepare_filename(info)
            return filename

    """
    def chat_get(self, YT_url):
        video_id = self.get_video_id(YT_url)
        livechat = pytchat.create(video_id=video_id)
        datelist = []
        while livechat.is_alive():
            chatdata = livechat.get()
            if (len(chatdata.items) > 0):
                for c in chatdata.items:
                    if c.elapsedTime[0] != "-":
                        datelist.append(self.convert_to_seconds(c.elapsedTime))
                    else:
                        break
        return datelist
    """
    
    def chat_get(self, YT_url):
        def convert_to_seconds(time_str):
            """
            String型のデータを秒に変換
            """
            parts = time_str.split(":")
            if len(parts) == 3:
                hours, minutes, seconds = map(int, time_str.split(":"))
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(int, time_str.split(":"))
                return minutes * 60 + seconds
        # Downloadsフォルダのパス作成
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        output_template = os.path.join(downloads_dir, "%(id)s.mp4")
        
        # yt-dlp オプション設定
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_template,
            'writesubtitles': True,
            'skip_download': True
        }
        
        # 動画情報の取得とチャットJSONのダウンロード
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(YT_url, download=False)
            ydl.download([YT_url])
        
        # チャットログのファイルパス
        chat_file_path = os.path.join(downloads_dir, f"{info_dict['id']}.live_chat.json")
        datelist = []
        
        if not os.path.exists(chat_file_path):
            raise FileNotFoundError(f"チャットファイルが見つかりません: {chat_file_path}")
        
        # ファイルを1行ずつ読み込み、各チャットエントリをパース
        with open(chat_file_path, "r", encoding="UTF-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    chat_item = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # キー "elapsedTime" が直接あれば利用
                if "elapsedTime" in chat_item:
                    elapsed = chat_item["elapsedTime"]
                    if elapsed and not elapsed.startswith("-"):
                        try:
                            seconds = convert_to_seconds(elapsed)
                            datelist.append(seconds)
                        except ValueError:
                            continue
                # また、"replayChatItemAction" 配下にある場合
                elif "replayChatItemAction" in chat_item:
                    action = chat_item["replayChatItemAction"]
                    # "videoOffsetTimeMsec" があればそれを利用
                    if "videoOffsetTimeMsec" in action:
                        try:
                            offset_ms = int(action["videoOffsetTimeMsec"])
                            if offset_ms >= 0:
                                datelist.append(offset_ms // 1000)
                        except ValueError:
                            pass
                    # なければ "elapsedTime" を利用
                    elif "elapsedTime" in action:
                        elapsed = action["elapsedTime"]
                        if elapsed and not elapsed.startswith("-"):
                            try:
                                seconds = convert_to_seconds(elapsed)
                                datelist.append(seconds)
                            except ValueError:
                                continue
        return datelist


    def convert_to_seconds(self, time_str):
        """
        String型のデータを秒に変換。
        """
        parts = time_str.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        return 0

    def get_video_id(self, YT_url):
        """
        URLからvideo_idを抜き出す。
        """
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(YT_url, download=False)
            return info_dict.get("id", None)

    def create_graph(self, YT_url, data_interval, **kwargs):
        """
        グラフの作成。チャットデータを相対時間に補正してプロットします。
        """
        date_list = self.chat_get(YT_url)
        if not date_list:
            messagebox.showinfo("エラー", "チャットデータを取得できませんでした。")
            return

        # 最初のチャット時刻を0秒に補正して、動画の再生開始と一致させる
        start_time_raw = min(date_list)
        # date_list = [t - start_time_raw for t in date_list]  # 先頭を0に
        end_time = max(date_list)

        time_slots = []
        current_time = 0
        while current_time <= end_time:
            time_slots.append(current_time)
            current_time += data_interval

        data_counts = []
        for slot in time_slots:
            count = sum(1 for data in date_list if slot <= data < slot + data_interval)
            data_counts.append(count)

        self.ax.set_xlim(0, end_time)

        self.ax.clear()
        # print("時間スロット (秒) とコメント数:")
        # for time, count in zip(time_slots, data_counts):
        #     print(f"{time}: {count}")
        self.ax.plot(time_slots, data_counts)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)
        self.ax.set_facecolor("none")
        self.ax.set_ylim(0, max(data_counts) * 1.1)
        # 空白を削除するコードを追加
        self.ax.margins(x=0, y=0)
        self.figure.tight_layout(pad=0)
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.canvas.draw()

        kwargs["highlightcolor"] = "#2196F3"
        kwargs["thickness"] = 30
        graph_width = self.canvas.get_tk_widget().winfo_width()
        self.progress_bar.config(length=400)
        self.progress_bar.pack(fill=tk.X)

    def convert_to_time(self, second):
        """
        秒から時間に変換。
        """
        hours = second // 3600
        minutes = (second % 3600) // 60
        seconds = second % 60
        if hours == 0:
            if minutes == 0:
                return f"{seconds}"
            else:
                return f"{minutes}:{seconds}"
        else:
            return f"{hours}:{minutes}:{seconds}"

    def on_graph_click(self, event):
        """
        グラフ上をクリックした位置に応じてプログレスバーと動画の再生位置を変更する
        """
        width = self.graph_widget.winfo_width()
        if width == 0:
            return
        fraction = event.x / width
        self.progress_bar["value"] = fraction * 100
        self.set_video_position(fraction * 100)

    def on_closing(self):
        """
        ウィンドウが閉じられる際の処理
        """
        if self.playing_video:
            self.media_player.stop()
        self.media_player.release()
        self.quit()

    # def update_graph(self):
    #     if self.playing_video:
    #         current_time = self.media_player.get_time() // 1000
    #         #self.ax.axvline(x=current_time, color='red', linestyle='--')
    #         self.canvas.draw()
    #     self.after(1000, self.update_graph)

    def run(self):
        """
        アプリケーションのメインループ
        """
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_video_progress()
        # self.update_graph()
        self.mainloop()

if __name__ == "__main__":
    app = MediaPlayerApp()
    app.update_video_progress()
    app.run()