import gtk

import class_document
import numberentry
import dateentry
import subjects
import utility
from amirconfig import config
from database import Subject
from helpers import get_builder

class AddEditDoc:
    def __init__(self, number=0):
        self.builder = get_builder("document")
        
        self.window = self.builder.get_object("window1")
        self.window.set_title(_("Register new document"))
        
        self.date = dateentry.DateEntry()
        box = self.builder.get_object("datebox")
        box.add(self.date)
        self.date.show()
        
        self.code = numberentry.NumberEntry()
        box = self.builder.get_object("codebox")
        box.add(self.code)
        self.code.show()
        self.code.connect("activate", self.selectSubject)
        self.code.set_tooltip_text(_("Press Enter to see available subjects."))
        
        self.amount = numberentry.NumberEntry()
        box = self.builder.get_object("amountbox")
        box.add(self.amount)
        self.amount.set_activates_default(True)
        self.amount.show()
        
        self.treeview = self.builder.get_object("treeview")
        #self.treeview.set_direction(gtk.TEXT_DIR_LTR)
        if gtk.widget_get_default_direction() == gtk.TEXT_DIR_RTL :
            halign = 1
        else:
            halign = 0
        self.liststore = gtk.ListStore(str, str, str, str, str, str)
        
        column = gtk.TreeViewColumn(_("Index"), gtk.CellRendererText(), text=0)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        self.treeview.append_column(column)
        column = gtk.TreeViewColumn(_("Subject Code"), gtk.CellRendererText(), text=1)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        self.treeview.append_column(column)
        column = gtk.TreeViewColumn(_("Subject Name"), gtk.CellRendererText(), text=2)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        
        money_cell_renderer = gtk.CellRendererText()
        #money_cell_renderer.set_alignment(1.0, 0.5) #incompatible with pygtk2.16
        
        self.treeview.append_column(column)
        column = gtk.TreeViewColumn(_("Debt"), money_cell_renderer, text=3)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        self.treeview.append_column(column)
        column = gtk.TreeViewColumn(_("Credit"), money_cell_renderer, text=4)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        self.treeview.append_column(column)
        column = gtk.TreeViewColumn(_("Description"), gtk.CellRendererText(), text=5)
        column.set_alignment(halign)
        column.set_spacing(5)
        column.set_resizable(True)
        self.treeview.append_column(column)

        self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        
        self.debt_sum   = 0
        self.credit_sum = 0
        self.numrows    = 0

        self.cl_document = class_document.Document()

        if number > 0:
            if self.cl_document.set_bill(number):
                self.showRows()
                self.window.set_title(_("Edit document"))
            else:
                numstring = utility.localizeNumber(self.cl_document.number)
                msg = _("No document found with number %s\nDo you want to register a document with this number?") % numstring
                msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, msg)
                msgbox.set_title(_("No Documents found"))
                result = msgbox.run()
                msgbox.destroy()
                if result == gtk.RESPONSE_CANCEL:
                    return
                else:
                    self.builder.get_object("docnumber").set_text (numstring)
    
        self.treeview.set_model(self.liststore)
        self.window.show_all()
        
        if self.cl_document.permanent:
            self.builder.get_object("editable").hide()
            self.builder.get_object("non-editable").show()
        else:
            self.builder.get_object("editable").show()
            self.builder.get_object("non-editable").hide()
        
        self.builder.connect_signals(self)
        #self.connect("database-changed", self.dbChanged)
        
    def showRows(self):
        self.date.showDateObject(self.cl_document.date)
        
        rows = self.cl_document.get_notebook_rows()
        for n, s in rows:
            self.numrows += 1
            if n.value < 0:
                value = -(n.value)
                debt = utility.showNumber(value)
                credit = utility.showNumber(0)
                self.debt_sum += value
            else:
                credit = utility.showNumber(n.value)
                debt = utility.showNumber(0)
                self.credit_sum += n.value
                
            code = s.code
            numrows = str(self.numrows)
            if config.digittype == 1:
                code = utility.convertToPersian(code)
                numrows = utility.convertToPersian(numrows)
            self.liststore.append((numrows, code, s.name, debt, credit, n.desc))
            
        docnum = utility.localizeNumber(self.cl_document.number)
        self.builder.get_object("docnumber").set_text (docnum)
        self.builder.get_object("debtsum").set_text (utility.showNumber(self.debt_sum))
        self.builder.get_object("creditsum").set_text (utility.showNumber(self.credit_sum))
        if self.debt_sum > self.credit_sum:
            diff = self.debt_sum - self.credit_sum
        else:
            diff = self.credit_sum - self.debt_sum
        self.builder.get_object("difference").set_text (utility.showNumber(diff))
        
    def addRow(self, sender):
        dialog = self.builder.get_object("dialog1")
        dialog.set_title(_("Add new row"))
        self.code.set_text("")
        
        desc = self.builder.get_object("desc")
        
        result = dialog.run()
        if result == 1:
            type = not (self.builder.get_object("debtor").get_active() == True)
                
            code = self.code.get_text()
            amount = self.amount.get_text()
            if code != '' and amount != '':
                self.saveRow(utility.convertToLatin(code),
                             int(unicode(amount)),
                             type,
                             desc.get_text())
        dialog.hide()
    
    def editRow(self, sender):
        dialog = self.builder.get_object("dialog1")
        dialog.set_title(_("Edit row"))
        
        selection = self.treeview.get_selection()
        iter = selection.get_selected()[1]
        
        if iter != None :
            code    = self.liststore.get(iter, 1)[0]
            debt    = self.liststore.get(iter, 3)[0].replace(",", "")
            credit  = self.liststore.get(iter, 4)[0].replace(",", "")
            desctxt = self.liststore.get(iter, 5)[0]
            
            if int(unicode(debt)) != 0:
                self.builder.get_object("debtor").set_active(True)
                self.amount.set_text(debt)
            else:
                self.builder.get_object("creditor").set_active(True)
                self.amount.set_text(credit)
                
            self.code.set_text(code)
            desc = self.builder.get_object("desc")
            desc.set_text(desctxt)
        
            result = dialog.run()
            if result == 1:
                type = not (self.builder.get_object("debtor").get_active() == True)
                    
                if int(unicode(debt)) != 0:
                    self.debt_sum -= int(unicode(debt))
                else:
                    self.credit_sum -= int(unicode(credit))
                    
                code = self.code.get_text()
                amount = self.amount.get_text()
                if code != '' and amount != '':
                    self.saveRow(utility.convertToLatin(code),
                                 int(unicode(amount)),
                                 int(type),
                                 desc.get_text(),
                                 iter)
            
            dialog.hide()
        
    #TODO add progress bar
    def saveRow(self, code, amount, type, desc, iter=None):
        query = config.db.session.query(Subject).select_from(Subject)
        query = query.filter(Subject.code == code)
        sub = query.first()
        if sub == None:
            if config.digittype == 1:
                code = utility.convertToPersian(code)
            errorstr = _("No subject is registered with the code: %s") % code
            msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, errorstr)
            msgbox.set_title(_("No subjects found"))
            msgbox.run()
            msgbox.destroy()
            return
            
        if sub.type != 2:
            type = sub.type
        
        debt   = "0"
        credit = "0"

        if config.digittype == 1:
            debt   = utility.convertToPersian(debt)
            credit = utility.convertToPersian(credit)
            code   = utility.convertToPersian(code)
        
        if type == 0:
            debt = utility.showNumber(amount)
            self.debt_sum += amount
        else:
            if type == 1:
                credit = utility.showNumber(amount)
                self.credit_sum += amount
                 
        if iter != None:
            self.liststore.set (iter, 1, code, 2, sub.name, 3, debt, 4, credit, 5, desc)
        else :
            self.numrows += 1
            numrows = str(self.numrows)
            if config.digittype == 1:
                numrows = utility.convertToPersian(numrows)
            self.liststore.append ((numrows, code, sub.name, debt, credit, desc))
            
        self.builder.get_object("debtsum").set_text (utility.showNumber(self.debt_sum))
        self.builder.get_object("creditsum").set_text (utility.showNumber(self.credit_sum))
        if self.debt_sum > self.credit_sum:
            diff = self.debt_sum - self.credit_sum
        else:
            diff = self.credit_sum - self.debt_sum
        self.builder.get_object("difference").set_text (utility.showNumber(diff))
    
    def deleteRow(self, sender):
        selection = self.treeview.get_selection()
        iter = selection.get_selected()[1]
        if iter != None :
            msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, 
                                       _("Are you sure to remove this row?"))
            msgbox.set_title(_("Are you sure?"))
            result = msgbox.run();
            if result == gtk.RESPONSE_OK :
                
                debt   = int(unicode(self.liststore.get(iter, 3)[0].replace(",", "")))
                credit = int(unicode(self.liststore.get(iter, 4)[0].replace(",", "")))
                index  = int(unicode(self.liststore.get(iter, 0)[0]))
                res    = self.liststore.remove(iter)
                #Update index of next rows
                if res:
                    while iter != None:
                        strindex = str(index)
                        if config.digittype == 1:
                            strindex = utility.convertToPersian(strindex)
                        self.liststore.set_value (iter, 0, strindex)
                        index += 1
                        iter = self.liststore.iter_next(iter)
                self.numrows -= 1;
                
                self.debt_sum -= debt
                self.credit_sum -= credit
                self.builder.get_object("debtsum").set_text (utility.showNumber(self.debt_sum))
                self.builder.get_object("creditsum").set_text (utility.showNumber(self.credit_sum))
                if self.debt_sum > self.credit_sum:
                    diff = self.debt_sum - self.credit_sum
                else:
                    diff = self.credit_sum - self.debt_sum
                self.builder.get_object("difference").set_text (utility.showNumber(diff))
            msgbox.destroy()
    
    def saveDocument(self, sender):
        sender.grab_focus()
        if self.numrows == 0:
            msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 
                                       _("Document should not be empty"))
            msgbox.set_title(_("Can not save document"))
            msgbox.run()
            msgbox.destroy()
            return
        
        iter = self.liststore.get_iter_first()
        debt_sum = 0
        credit_sum = 0
        while iter != None :
            value = unicode(self.liststore.get(iter, 3)[0].replace(",", ""))
            debt_sum += int(value)
            value = unicode(self.liststore.get(iter, 4)[0].replace(",", ""))
            credit_sum += int(value)
            iter = self.liststore.iter_next(iter)
                
        if debt_sum != credit_sum:        
            msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, 
                                       _("Debt sum and Credit sum should be equal"))
            msgbox.set_title(_("Can not save document"))
            msgbox.run()
            msgbox.destroy()
            return
        
        self.cl_document.new_date = self.date.getDateObject()
        
        #TODO if number is not equal to the maximum BigInteger value, prevent bill registration.
                
        iter = self.liststore.get_iter_first()
        while iter != None :
            code = utility.convertToLatin(self.liststore.get(iter, 1)[0])
            debt = unicode(self.liststore.get(iter, 3)[0].replace(",", ""))
            value = -(int(debt))
            if value == 0 :
                credit = unicode(self.liststore.get(iter, 4)[0].replace(",", ""))
                value = int(credit)
            desctxt = unicode(self.liststore.get(iter, 5)[0])
            
            query = config.db.session.query(Subject).select_from(Subject)
            query = query.filter(Subject.code == code)
            subject_id = query.first().id
            
            self.cl_document.add_notebook(subject_id, value, desctxt)
            
            iter = self.liststore.iter_next(iter)

        self.cl_document.save()
        
        docnum = utility.localizeNumber(self.cl_document.number)
        self.builder.get_object("docnumber").set_text (docnum)
        
        msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, 
                                   _("Document saved with number %s.") % docnum)
        msgbox.set_title(_("Successfully saved"))
        msgbox.run()
        msgbox.destroy()
        
    def makePermanent(self, sender):
        if self.cl_document.id > 0 :
            self.cl_document.set_permanent(True)
            self.builder.get_object("editable").hide()
            self.builder.get_object("non-editable").show()
        else:
            msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO, gtk.BUTTONS_OK, 
                                   _("You should save the document before make it permanent"))
            msgbox.set_title(_("Document is not saved"))
            msgbox.run()
            msgbox.destroy()
 
    def makeTemporary(self, sender):
        msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL, 
                                   _("Are you sure to make this document temporary?"))
        msgbox.set_title(_("Are you sure?"))
        result = msgbox.run();
        msgbox.destroy()
        
        if result == gtk.RESPONSE_OK and self.cl_document.id > 0 :
            self.cl_document.set_permanent(False)
            self.builder.get_object("non-editable").hide()
            self.builder.get_object("editable").show()
                           
    def deleteDocument(self, sender):
        if self.cl_document.id == 0 :
            return
        
        msgbox = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK_CANCEL,
                                   _("Are you sure to delete the whole document?"))
        msgbox.set_title(_("Are you sure?"))
        result = msgbox.run();
        
        if result == gtk.RESPONSE_OK :
            self.cl_document.delete()
            self.window.destroy()
        msgbox.destroy() 

    def selectSubject(self, sender):
        subject_win = subjects.Subjects()
        code = self.code.get_text()
        subject_win.highlightSubject(code)
        subject_win.connect("subject-selected", self.subjectSelected)
        
    def subjectSelected(self, sender, id, code, name):
        if config.digittype == 1:
            code = utility.convertToPersian(code)
        self.code.set_text(code)
        sender.window.destroy()      
          
    def dbChanged(self, sender, active_dbpath):
        self.window.destroy()
