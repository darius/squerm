(define (main)
  (let ((tally< (start-election (list alice bob carol))))
    (with-new-channel
     (lambda (<k k<)
       (tally< k<)
       (print (<k))))))

(define (alice v<) (v< 'obama))
(define (bob v<)   (v< 'mccain))
(define (carol v<) (v< 'obama))

(define (start-election voters)
  (with-new-slate
   (lambda (vote< tally<)
     (send-ballots voters vote<)
     tally<)))

(define (send-ballots voters vote<)
  (for-each (lambda (voter) (voter (make-ballot vote<)))
            voters))
              
(define (make-ballot vote<)
  (sprout-spawn complaining-keeper (lambda (<v v<)
                                     (vote< (<v)))))

(define (with-new-slate k)
  (let ((pair (sprout2-spawn complaining-keeper
                             (lambda (<vote <tally)
                               (slate-loop <vote <tally '())))))
    (let ((vote< (car pair))
          (tally< (cadr pair)))
      (k vote< tally<))))

(define (slate-loop <vote <tally pairs)
  (let loop ((pairs pairs))
    (choose `((,<vote ,(lambda (choice)
                         (loop (incr choice pairs))))
              (,<tally ,(lambda (k<)
                          (k< pairs)
                          (loop pairs)))))))

(define (incr choice pairs)
  (cond ((null? pairs)
         (list (list choice 1)))
        ((equal? (caar pairs) choice)
         (cons (list (caar pairs) (+ 1 (cadar pairs)))
               (cdr pairs)))
        (else (cons (car pairs)
                    (incr choice (cdr pairs))))))

(define (with-new-channel f)
  (let ((pair (sprout)))
    (f (car pair) (cadr pair))))

(define (sprout-spawn keeper fn)
  (with-new-channel
   (lambda (<setup setup<)
     (spawn keeper (lambda ()
                     (with-new-channel
                      (lambda (<ch ch<)
                        (setup< ch<)
                        (fn <ch ch<)))))
     (<setup))))

(define (sprout2-spawn keeper fn)       ;ughyugh
  (with-new-channel
   (lambda (<setup setup<)
     (spawn keeper (lambda ()
                     (with-new-channel
                      (lambda (<ch1 ch1<)
                        (with-new-channel
                         (lambda (<ch2 ch2<)
                           (setup< (list ch1< ch2<))
                           (fn <ch1 <ch2)))))))
     (<setup))))

(define (for-each f xs)
  (cond ((null? xs) 'ok)
        (else
         (f (car xs))
         (for-each f (cdr xs)))))
