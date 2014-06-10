(define (main)
  (let ((tally< (start-election (list alice bob carol))))
    (mlet ((<k k<) (sprout))
      (tally< k<)
      (print (<k)))))

(define (alice v<) (v< 'obama))
(define (bob v<)   (v< 'mccain))
(define (carol v<) (v< 'obama))

(define (start-election voters)
  (mlet ((vote< tally<) (make-slate))
    (send-ballots voters vote<)
    tally<))

(define (send-ballots voters vote<)
  (for-each (lambda (voter) (voter (make-ballot vote<)))
            voters))
              
(define (make-ballot vote<)
  ;; Return a sender that forwards to vote< once (and no more).
  (sprout-spawn complaining-keeper (lambda (<v v<)
                                     (vote< (<v)))))

(define (make-slate)
  (sprout2-spawn complaining-keeper
                 (lambda (<vote <tally)
                   (slate-loop <vote <tally '()))))

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

(define (sprout-spawn keeper fn)
  (mlet ((<setup setup<) (sprout))
    (spawn keeper (lambda ()
                    (mlet ((<ch ch<) (sprout))
                      (setup< ch<)
                      (fn <ch ch<))))
    (<setup)))

(define (sprout2-spawn keeper fn)       ;ughyugh
  (mlet ((<setup setup<) (sprout))
    (spawn keeper (lambda ()
                    (mlet ((<ch1 ch1<) (sprout))
                      (mlet ((<ch2 ch2<) (sprout))
                        (setup< (list ch1< ch2<))
                        (fn <ch1 <ch2)))))
    (<setup)))

(define (for-each f xs)
  (cond ((null? xs) 'ok)
        (else
         (f (car xs))
         (for-each f (cdr xs)))))
