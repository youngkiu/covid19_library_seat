import os
import datetime
import wx
import wxFormBuilder.noname as gui
import pandas as pd


class MainApp(gui.MyFrame1):
    HALLWAY_FILE_NAME = '복도.csv'

    def __init__(self, parent):
        gui.MyFrame1.__init__(self, parent)

        self.m_button3.Disable()
        self.m_button1.SetFocus()

        self.__vertical_vacancy = None
        self.__horizontal_vacancy = None
        self.__not_reusable_time = None
        self.__max_utilization = None
        self.__running = False
        self.__reseving = False

        cols = self.m_grid1.GetNumberCols()
        rows = self.m_grid1.GetNumberRows()

        if os.path.exists(MainApp.HALLWAY_FILE_NAME):
            seat_state = self.__load_seat_state()
            csv_rows, csv_cols = seat_state.shape
            assert cols == csv_cols and rows == csv_rows
        else:
            seat_state = pd.DataFrame(index=range(rows), columns=range(cols))
            seat_state.to_csv(MainApp.HALLWAY_FILE_NAME)

        self.__num_of_seat = cols * rows
        for row in range(rows):
            for col in range(cols):
                if seat_state.iloc[row][col] == '복도':
                    self.__num_of_seat -= 1
        self.__num_of_use = 0

        self.__seat_state = seat_state

    def __load_seat_state(self):
        seat_state = pd.read_csv(MainApp.HALLWAY_FILE_NAME, index_col=0, keep_default_na=False)
        rows, cols = seat_state.shape
        for row in range(rows):
            for col in range(cols):
                self.m_grid1.SetCellValue(row, col, seat_state.iloc[row][col])
        return seat_state

    def __check_vertical(self, seat_state, row, col, rows):
        for v in range(row - self.__vertical_vacancy, row + 1 + self.__vertical_vacancy):
            if v < 0 or v >= rows:
                continue
            if seat_state.iloc[v][col] == '사용중':
                return False
        return True

    def __check_horizontal(self, seat_state, row, col, cols):
        for h in range(col - self.__horizontal_vacancy, col + 1 + self.__horizontal_vacancy):
            if h < 0 or h >= cols:
                continue
            if seat_state.iloc[row][h] == '사용중':
                return False
        return True

    def __find_available_seat(self):
        # check utilization
        utilization = self.__num_of_use / self.__num_of_seat * 100
        if utilization > self.__max_utilization:
            dial = wx.MessageDialog(
                self,
                'Reach max utilization',
                'Wait',
                wx.ICON_WARNING
            )
            dial.ShowModal()
            return False

        seat_state = self.__seat_state
        rows, cols = seat_state.shape
        now = datetime.datetime.now()
        for row in range(rows):
            for col in range(cols):
                # check datetime
                if type(seat_state.iloc[row][col]) is datetime.datetime:
                    delta = datetime.timedelta(hours=self.__not_reusable_time)
                    if now < seat_state.iloc[row][col] + delta:
                        continue

                if seat_state.iloc[row][col] == '복도':
                    continue

                # check vertical
                if self.__check_vertical(seat_state, row, col, rows) == False:
                    continue

                # check horizontal
                if self.__check_horizontal(seat_state, row, col, cols) == False:
                    continue

                self.m_grid1.SetCellValue(row, col, '사용 가능')

        return True

    def __display_running_state(self, seat_state):
        cols = self.m_grid1.GetNumberCols()
        rows = self.m_grid1.GetNumberRows()
        for row in range(rows):
            for col in range(cols):
                if type(seat_state.iloc[row][col]) is datetime.datetime:
                    self.m_grid1.SetCellValue(row, col, seat_state.iloc[row][col].strftime('%H시 %M분'))
                else:
                    self.m_grid1.SetCellValue(row, col, seat_state.iloc[row][col])

    # Virtual event handlers, overide them in your derived class
    def m_button1OnButtonClick(self, event):
        if self.__running is False:
            self.__vertical_vacancy = int(self.m_checkBox1.GetValue())
            self.__horizontal_vacancy = int(self.m_textCtrl1.GetValue())
            self.__not_reusable_time = int(self.m_textCtrl2.GetValue())
            self.__max_utilization = int(self.m_textCtrl3.GetValue())

            self.m_staticText4.Disable()
            self.m_checkBox1.Disable()
            self.m_staticText1.Disable()
            self.m_textCtrl1.Disable()
            self.m_staticText2.Disable()
            self.m_textCtrl2.Disable()
            self.m_staticText3.Disable()
            self.m_textCtrl3.Disable()
            self.m_button3.Enable()

            text_string = f'앞뒤: {self.__vertical_vacancy}칸,  옆: {self.__horizontal_vacancy}칸,  재사용 불가: {self.__not_reusable_time}시간,  최대 사용률: {self.__max_utilization}%'
            self.m_statusBar1.SetStatusText(text_string)

            self.m_button1.SetLabel('종료')
            self.__running = True
            self.__reseving = False
            self.__num_of_use = 0
        else:
            self.m_staticText4.Enable()
            self.m_checkBox1.Enable()
            self.m_staticText1.Enable()
            self.m_textCtrl1.Enable()
            self.m_staticText2.Enable()
            self.m_textCtrl2.Enable()
            self.m_staticText3.Enable()
            self.m_textCtrl3.Enable()
            self.m_button3.Disable()

            self.m_statusBar1.SetStatusText('')

            self.m_button1.SetLabel('시작')
            self.__running = False
            self.__seat_state = self.__load_seat_state()  # for reset state

    def m_button3OnButtonClick(self, event):
        if self.__reseving is False:
            if self.__find_available_seat():
                self.m_button3.SetLabel('예약 취소')
                self.__reseving = True
        else:
            self.__display_running_state(self.__seat_state)
            self.m_button3.SetLabel('사용가능 자리')
            self.__reseving = False

    def __show_popupmenu(self, event):
        row = event.Row
        col = event.Col

        seat_state = self.__seat_state

        # https://stackoverflow.com/a/39000965/6572046
        if self.__running == False:
            if seat_state.iloc[row][col] == '복도':
                entry = '복도 취소'
                data = ''
            else:
                entry = '복도'
                data = '복도'
        else:
            if self.m_grid1.GetCellValue(row, col) == '사용 가능':
                entry = '예약'
                data = '사용중'
            elif self.m_grid1.GetCellValue(row, col) == '사용중':
                entry = '반납'
                data = datetime.datetime.now()
            else:
                entry = ''
                data = ''

        if entry:
            popupmenu = wx.Menu()
            menuItem = popupmenu.Append(-1, entry)
            wrapper = lambda event: self.OnStuff(event, row, col, data)
            self.Bind(wx.EVT_MENU, wrapper, menuItem)
            self.PopupMenu(popupmenu)

    def OnStuff(self, event, row, col, data):
        seat_state = self.__seat_state
        if self.__running == False:
            if data == '복도':
                self.__num_of_seat -= 1
            else:
                assert not data
                self.__num_of_seat += 1

            seat_state.iloc[row][col] = data
            seat_state.to_csv(MainApp.HALLWAY_FILE_NAME)
            self.m_grid1.SetCellValue(row, col, seat_state.iloc[row][col])
        elif data:
            if type(data) is datetime.datetime:
                self.__num_of_use -= 1
            elif data == '사용중':
                self.__num_of_use += 1

            seat_state.iloc[row][col] = data
            self.__display_running_state(seat_state)
            self.m_button3.SetLabel('사용가능 자리')
            self.__reseving = False

    def m_grid1OnGridCellLeftClick(self, event):
        self.__show_popupmenu(event)

    def m_grid1OnGridCellRightClick(self, event):
        self.__show_popupmenu(event)


if __name__ == '__main__':
    app = wx.App()
    window = MainApp(None)
    window.Show(True)
    app.MainLoop()
